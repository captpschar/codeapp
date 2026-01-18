"""
Flask-based Inspection Photo Review Application.
"""

import sys
import os
import io
import base64
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.app_state import AppState
from core.inspection_item import InspectionItem, ItemStatus, MatchType, ConfidenceLevel
from core.config_manager import CodeFolder

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Global app state
_app_state: Optional[AppState] = None
_processing_status: Dict[str, Any] = {
    'running': False,
    'current_item': None,
    'progress': 0,
    'total': 0,
    'error': None
}
_export_status: Dict[str, Any] = {
    'running': False,
    'progress': 0,
    'total': 0,
    'error': None,
    'doc_url': None
}


def get_app_state() -> AppState:
    """Get or create global app state."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Dashboard page."""
    state = get_app_state()
    items = state.queue.get_all_items()

    stats = {
        'pending': len([i for i in items if i.status == ItemStatus.PENDING]),
        'processing': len([i for i in items if i.status == ItemStatus.PROCESSING]),
        'review_ready': len([i for i in items if i.status == ItemStatus.REVIEW_READY]),
        'approved': len([i for i in items if i.status == ItemStatus.APPROVED]),
        'exported': len([i for i in items if i.status == ItemStatus.EXPORTED]),
        'error': len([i for i in items if i.status == ItemStatus.ERROR]),
        'total': len(items)
    }

    configured = state.config.is_configured()
    return render_template('index.html', stats=stats, configured=configured)


@app.route('/triage')
def triage():
    """Triage page - load images, edit, add to queue."""
    state = get_app_state()
    code_folders = state.config.code_folders
    return render_template('triage.html', code_folders=code_folders)


@app.route('/processing')
def processing():
    """Processing page - AI analysis monitoring."""
    return render_template('processing.html')


@app.route('/review')
def review():
    """Review page - verify AI results, approve items."""
    return render_template('review.html')


@app.route('/export')
def export():
    """Export page - export to Google Docs."""
    return render_template('export.html')


@app.route('/settings')
def settings():
    """Settings page."""
    state = get_app_state()
    config = state.config
    return render_template('settings.html', config=config)


# ============================================================================
# TRIAGE API ENDPOINTS
# ============================================================================

@app.route('/api/triage/state', methods=['GET'])
def get_triage_state():
    """Get current triage state (folder, files, index)."""
    state = get_app_state()
    ts = state.triage_state

    return jsonify({
        'folder': str(ts.image_folder) if ts.image_folder else None,
        'files': [str(f) for f in ts.image_files],
        'current_index': ts.current_index,
        'total': len(ts.image_files),
        'selected_folders': list(ts.selected_folders),
        'selected_chapters': ts.selected_chapters
    })


@app.route('/api/triage/load-folder', methods=['POST'])
def load_folder():
    """Load images from a folder."""
    data = request.json
    folder_path = data.get('folder_path')

    if not folder_path:
        return jsonify({'error': 'No folder path provided'}), 400

    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        return jsonify({'error': 'Invalid folder path'}), 400

    # Find image files
    extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    files = sorted([
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])

    if not files:
        return jsonify({'error': 'No image files found in folder'}), 400

    # Update triage state
    state = get_app_state()
    state.triage_state.image_folder = path
    state.triage_state.image_files = files
    state.triage_state.current_index = 0

    return jsonify({
        'success': True,
        'folder': str(path),
        'files': [str(f) for f in files],
        'total': len(files)
    })


@app.route('/api/triage/load-files', methods=['POST'])
def load_files():
    """Load specific image files."""
    data = request.json
    file_paths = data.get('file_paths', [])

    if not file_paths:
        return jsonify({'error': 'No files provided'}), 400

    files = []
    for fp in file_paths:
        path = Path(fp)
        if path.exists() and path.is_file():
            files.append(path)

    if not files:
        return jsonify({'error': 'No valid files found'}), 400

    state = get_app_state()
    state.triage_state.image_folder = files[0].parent if files else None
    state.triage_state.image_files = files
    state.triage_state.current_index = 0

    return jsonify({
        'success': True,
        'files': [str(f) for f in files],
        'total': len(files)
    })


@app.route('/api/triage/navigate', methods=['POST'])
def navigate_image():
    """Navigate to a different image (prev/next/index)."""
    data = request.json
    action = data.get('action')  # 'prev', 'next', 'first', 'last', or 'goto'
    index = data.get('index', 0)

    state = get_app_state()
    ts = state.triage_state

    if not ts.image_files:
        return jsonify({'error': 'No images loaded'}), 400

    total = len(ts.image_files)

    if action == 'prev':
        ts.current_index = max(0, ts.current_index - 1)
    elif action == 'next':
        ts.current_index = min(total - 1, ts.current_index + 1)
    elif action == 'first':
        ts.current_index = 0
    elif action == 'last':
        ts.current_index = total - 1
    elif action == 'goto':
        ts.current_index = max(0, min(total - 1, index))

    return jsonify({
        'current_index': ts.current_index,
        'total': total,
        'file': str(ts.image_files[ts.current_index])
    })


@app.route('/api/triage/current-image')
def get_current_image():
    """Get the current image as base64."""
    state = get_app_state()
    ts = state.triage_state

    if not ts.image_files or ts.current_index >= len(ts.image_files):
        return jsonify({'error': 'No image selected'}), 400

    image_path = ts.image_files[ts.current_index]

    try:
        with open(image_path, 'rb') as f:
            data = f.read()

        ext = image_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        mime = mime_types.get(ext, 'image/jpeg')

        b64 = base64.b64encode(data).decode()

        return jsonify({
            'success': True,
            'image': f'data:{mime};base64,{b64}',
            'filename': image_path.name,
            'path': str(image_path),
            'index': ts.current_index,
            'total': len(ts.image_files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/triage/edit-image', methods=['POST'])
def edit_image():
    """Apply edits to an image and return the result."""
    data = request.json
    image_path = data.get('image_path')
    edits = data.get('edits', {})

    if not image_path:
        return jsonify({'error': 'No image path'}), 400

    try:
        img = Image.open(image_path)

        # Apply rotation
        rotation = edits.get('rotation', 0)
        if rotation:
            img = img.rotate(-rotation, expand=True)

        # Apply brightness
        brightness = edits.get('brightness', 1.0)
        if brightness != 1.0:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)

        # Apply contrast
        contrast = edits.get('contrast', 1.0)
        if contrast != 1.0:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)

        # Apply crop (coordinates as percentage)
        crop = edits.get('crop')
        if crop:
            w, h = img.size
            left = int(crop['x'] * w)
            top = int(crop['y'] * h)
            right = int((crop['x'] + crop['width']) * w)
            bottom = int((crop['y'] + crop['height']) * h)
            img = img.crop((left, top, right, bottom))

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        b64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{b64}',
            'width': img.width,
            'height': img.height
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/triage/add-to-queue', methods=['POST'])
def add_to_queue():
    """Add current image with metadata to processing queue."""
    data = request.json

    state = get_app_state()
    ts = state.triage_state

    if not ts.image_files or ts.current_index >= len(ts.image_files):
        return jsonify({'error': 'No image selected'}), 400

    original_path = ts.image_files[ts.current_index]

    try:
        # Get edit parameters
        edits = data.get('edits', {})
        location = data.get('location', '')
        description = data.get('description', '')
        selected_folders = data.get('selected_folders', [])
        selected_chapters = data.get('selected_chapters', [])

        # Load and edit image
        img = Image.open(original_path)

        # Apply edits
        rotation = edits.get('rotation', 0)
        if rotation:
            img = img.rotate(-rotation, expand=True)

        brightness = edits.get('brightness', 1.0)
        if brightness != 1.0:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)

        contrast = edits.get('contrast', 1.0)
        if contrast != 1.0:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)

        crop = edits.get('crop')
        if crop:
            w, h = img.size
            left = int(crop['x'] * w)
            top = int(crop['y'] * h)
            right = int((crop['x'] + crop['width']) * w)
            bottom = int((crop['y'] + crop['height']) * h)
            img = img.crop((left, top, right, bottom))

        # Save edited image
        output_dir = state.config.output_directory
        edited_dir = Path(output_dir) / 'edited'
        edited_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        edited_filename = f"{original_path.stem}_{timestamp}.jpg"
        edited_path = edited_dir / edited_filename

        img.save(edited_path, format='JPEG', quality=90)

        # Create inspection item
        item = InspectionItem()
        item.photo_original_path = str(original_path)
        item.photo_edited_path = str(edited_path)
        item.user_location = location
        item.user_description = description
        item.selected_code_folders = selected_folders
        item.selected_chapters = selected_chapters
        item.status = ItemStatus.PENDING

        # Add to queue
        state.queue.add_item(item)

        return jsonify({
            'success': True,
            'item_id': item.id,
            'message': 'Added to queue'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/triage/queue')
def get_queue():
    """Get current queue items."""
    state = get_app_state()
    items = state.queue.get_all_items()

    return jsonify({
        'items': [
            {
                'id': item.id,
                'filename': Path(item.photo_original_path).name if item.photo_original_path else 'Unknown',
                'location': item.user_location,
                'status': item.status.value,
                'created_at': item.created_at.isoformat() if item.created_at else None
            }
            for item in items
        ]
    })


@app.route('/api/triage/remove-from-queue', methods=['POST'])
def remove_from_queue():
    """Remove item from queue."""
    data = request.json
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'error': 'No item ID'}), 400

    state = get_app_state()
    state.queue.remove_item(item_id)

    return jsonify({'success': True})


@app.route('/api/triage/set-selections', methods=['POST'])
def set_selections():
    """Update selected folders and chapters."""
    data = request.json

    state = get_app_state()
    ts = state.triage_state

    if 'selected_folders' in data:
        ts.selected_folders = set(data['selected_folders'])
    if 'selected_chapters' in data:
        ts.selected_chapters = data['selected_chapters']

    return jsonify({'success': True})


@app.route('/api/code-folders/<folder_name>/chapters')
def get_folder_chapters(folder_name):
    """Get PDF chapters in a code folder."""
    state = get_app_state()

    folder = None
    for f in state.config.code_folders:
        if f.name == folder_name:
            folder = f
            break

    if not folder:
        return jsonify({'error': 'Folder not found'}), 404

    path = Path(folder.path)
    if not path.exists():
        return jsonify({'error': 'Folder path does not exist'}), 404

    pdfs = sorted([f.name for f in path.glob('*.pdf')])

    return jsonify({
        'folder': folder_name,
        'chapters': pdfs
    })


# ============================================================================
# PROCESSING API ENDPOINTS
# ============================================================================

@app.route('/api/processing/status')
def get_processing_status():
    """Get current processing status."""
    global _processing_status
    state = get_app_state()

    pending = len([i for i in state.queue.get_all_items() if i.status == ItemStatus.PENDING])

    return jsonify({
        'running': _processing_status['running'],
        'current_item': _processing_status['current_item'],
        'progress': _processing_status['progress'],
        'total': _processing_status['total'],
        'pending': pending,
        'error': _processing_status['error']
    })


@app.route('/api/processing/start', methods=['POST'])
def start_processing():
    """Start AI processing of pending items."""
    global _processing_status

    if _processing_status['running']:
        return jsonify({'error': 'Processing already running'}), 400

    state = get_app_state()
    pending_items = [i for i in state.queue.get_all_items() if i.status == ItemStatus.PENDING]

    if not pending_items:
        return jsonify({'error': 'No pending items'}), 400

    if not state.config.gemini_api_key:
        return jsonify({'error': 'Gemini API key not configured'}), 400

    # Start processing in background thread
    _processing_status = {
        'running': True,
        'current_item': None,
        'progress': 0,
        'total': len(pending_items),
        'error': None
    }

    thread = threading.Thread(target=_run_processing, args=(pending_items,))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'total': len(pending_items)})


@app.route('/api/processing/stop', methods=['POST'])
def stop_processing():
    """Stop processing."""
    global _processing_status
    _processing_status['running'] = False
    return jsonify({'success': True})


def _run_processing(items: List[InspectionItem]):
    """Background processing function."""
    global _processing_status

    state = get_app_state()

    from services.ai_service.gemini_client import GeminiClient
    from services.ai_service.prompt_templates import SYSTEM_PROMPT_CODE_ANALYSIS, build_analysis_prompt
    from services.ai_service.response_parser import parse_analysis_response

    client = GeminiClient(
        api_key=state.config.gemini_api_key,
        model_name=state.config.ai_settings.model_name
    )

    for i, item in enumerate(items):
        if not _processing_status['running']:
            break

        _processing_status['current_item'] = Path(item.photo_original_path).name if item.photo_original_path else 'Unknown'
        _processing_status['progress'] = i

        try:
            # Update status to processing
            item.status = ItemStatus.PROCESSING
            state.queue.update_item(item)

            # Build prompts
            system_prompt = SYSTEM_PROMPT_CODE_ANALYSIS
            user_prompt = build_analysis_prompt(
                description=item.user_description or '',
                location=item.user_location or ''
            )

            # Call AI
            image_path = item.photo_edited_path or item.photo_original_path
            response = client.generate_with_image(system_prompt, user_prompt, image_path)

            # Parse response
            parsed = parse_analysis_response(response)

            # Update item
            item.ai_code_reference = parsed.reference
            item.ai_violation_description = parsed.reasoning
            item.ai_match_type = parsed.match_type
            item.ai_confidence = parsed.confidence
            item.status = ItemStatus.REVIEW_READY
            state.queue.update_item(item)

        except Exception as e:
            item.status = ItemStatus.ERROR
            item.error_message = str(e)
            state.queue.update_item(item)
            _processing_status['error'] = str(e)

    _processing_status['running'] = False
    _processing_status['progress'] = len(items)


@app.route('/api/processing/items')
def get_processing_items():
    """Get all items with their processing status."""
    state = get_app_state()
    items = state.queue.get_all_items()

    return jsonify({
        'items': [
            {
                'id': item.id,
                'filename': Path(item.photo_original_path).name if item.photo_original_path else 'Unknown',
                'status': item.status.value,
                'error': item.error_message if item.status == ItemStatus.ERROR else None
            }
            for item in items
        ]
    })


# ============================================================================
# REVIEW API ENDPOINTS
# ============================================================================

@app.route('/api/review/items')
def get_review_items():
    """Get items ready for review."""
    state = get_app_state()
    items = state.queue.get_all_items()

    review_items = [i for i in items if i.status in (ItemStatus.REVIEW_READY, ItemStatus.APPROVED)]

    return jsonify({
        'items': [
            {
                'id': item.id,
                'filename': Path(item.photo_original_path).name if item.photo_original_path else 'Unknown',
                'location': item.user_location,
                'description': item.user_description,
                'status': item.status.value,
                'ai_reference': item.ai_code_reference,
                'ai_violation': item.ai_violation_description,
                'ai_confidence': item.ai_confidence.value if item.ai_confidence else None,
                'approved': item.status == ItemStatus.APPROVED,
                'snapshot_path': item.snapshot_path
            }
            for item in review_items
        ]
    })


@app.route('/api/review/item/<item_id>')
def get_review_item(item_id):
    """Get detailed item for review."""
    state = get_app_state()
    item = state.queue.get_item_by_id(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Get edited image as base64
    image_b64 = None
    if item.photo_edited_path and Path(item.photo_edited_path).exists():
        with open(item.photo_edited_path, 'rb') as f:
            image_b64 = f'data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}'

    # Get snapshot as base64 if exists
    snapshot_b64 = None
    if item.snapshot_path and Path(item.snapshot_path).exists():
        with open(item.snapshot_path, 'rb') as f:
            snapshot_b64 = f'data:image/png;base64,{base64.b64encode(f.read()).decode()}'

    return jsonify({
        'id': item.id,
        'filename': Path(item.photo_original_path).name if item.photo_original_path else 'Unknown',
        'location': item.user_location,
        'description': item.user_description,
        'status': item.status.value,
        'image': image_b64,
        'snapshot': snapshot_b64,
        'ai_reference': item.ai_code_reference,
        'ai_violation': item.ai_violation_description,
        'ai_confidence': item.ai_confidence.value if item.ai_confidence else None,
        'ai_match_type': item.ai_match_type.value if item.ai_match_type else None,
        'selected_chapters': item.selected_chapters,
        'selected_code_folders': item.selected_code_folders,
        'approved': item.status == ItemStatus.APPROVED
    })


@app.route('/api/review/approve', methods=['POST'])
def approve_item():
    """Approve or unapprove an item."""
    data = request.json
    item_id = data.get('item_id')
    approved = data.get('approved', True)

    state = get_app_state()
    item = state.queue.get_item_by_id(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if approved:
        item.status = ItemStatus.APPROVED
        item.approved_at = datetime.now()
    else:
        item.status = ItemStatus.REVIEW_READY
        item.approved_at = None

    state.queue.update_item(item)

    return jsonify({'success': True, 'status': item.status.value})


@app.route('/api/review/reprocess', methods=['POST'])
def reprocess_item():
    """Send item back to processing."""
    data = request.json
    item_id = data.get('item_id')

    state = get_app_state()
    item = state.queue.get_item_by_id(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    item.status = ItemStatus.PENDING
    item.ai_code_reference = ''
    item.ai_violation_description = ''
    item.ai_confidence = None
    item.ai_match_type = None
    state.queue.update_item(item)

    return jsonify({'success': True})


# ============================================================================
# PDF API ENDPOINTS
# ============================================================================

@app.route('/api/pdf/list')
def list_pdfs():
    """List available PDFs from code folders."""
    state = get_app_state()

    pdfs = []
    for folder in state.config.code_folders:
        path = Path(folder.path)
        if path.exists():
            for pdf in path.glob('*.pdf'):
                pdfs.append({
                    'folder': folder.name,
                    'name': pdf.name,
                    'path': str(pdf)
                })

    return jsonify({'pdfs': pdfs})


@app.route('/api/pdf/render', methods=['POST'])
def render_pdf_page():
    """Render a PDF page as image."""
    data = request.json
    pdf_path = data.get('pdf_path')
    page_num = data.get('page_num', 0)
    dpi = data.get('dpi', 150)

    if not pdf_path or not Path(pdf_path).exists():
        return jsonify({'error': 'PDF not found'}), 404

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            page_num = len(doc) - 1

        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img_data = pix.tobytes('png')
        b64 = base64.b64encode(img_data).decode()

        total_pages = len(doc)
        doc.close()

        return jsonify({
            'image': f'data:image/png;base64,{b64}',
            'page_num': page_num,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf/search', methods=['POST'])
def search_pdf():
    """Search for text in PDF."""
    data = request.json
    pdf_path = data.get('pdf_path')
    term = data.get('term')

    if not pdf_path or not term:
        return jsonify({'error': 'Missing pdf_path or term'}), 400

    if not Path(pdf_path).exists():
        return jsonify({'error': 'PDF not found'}), 404

    try:
        import fitz

        doc = fitz.open(pdf_path)
        results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            matches = page.search_for(term)
            for rect in matches:
                results.append({
                    'page': page_num,
                    'rect': [rect.x0, rect.y0, rect.x1, rect.y1]
                })

        doc.close()

        return jsonify({
            'found': len(results) > 0,
            'results': results,
            'first_page': results[0]['page'] if results else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf/snapshot', methods=['POST'])
def take_snapshot():
    """Take a snapshot of a PDF page region."""
    data = request.json
    item_id = data.get('item_id')
    pdf_path = data.get('pdf_path')
    page_num = data.get('page_num', 0)
    rect = data.get('rect')  # Optional highlight rect

    state = get_app_state()
    item = state.queue.get_item_by_id(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if not pdf_path or not Path(pdf_path).exists():
        return jsonify({'error': 'PDF not found'}), 404

    try:
        import fitz

        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # Render at high DPI for snapshot
        dpi = state.config.pdf_settings.snapshot_dpi
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        # Save snapshot
        output_dir = Path(state.config.output_directory) / 'snapshots'
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_path = output_dir / f'snapshot_{item_id}_{timestamp}.png'
        pix.save(str(snapshot_path))

        doc.close()

        # Update item
        item.snapshot_path = str(snapshot_path)
        state.queue.update_item(item)

        # Return as base64
        with open(snapshot_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()

        return jsonify({
            'success': True,
            'snapshot': f'data:image/png;base64,{b64}',
            'path': str(snapshot_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXPORT API ENDPOINTS
# ============================================================================

@app.route('/api/export/status')
def get_export_status():
    """Get export status."""
    global _export_status
    state = get_app_state()

    approved = len([i for i in state.queue.get_all_items() if i.status == ItemStatus.APPROVED])

    return jsonify({
        'running': _export_status['running'],
        'progress': _export_status['progress'],
        'total': _export_status['total'],
        'error': _export_status['error'],
        'doc_url': _export_status['doc_url'],
        'approved_count': approved
    })


@app.route('/api/export/preflight')
def export_preflight():
    """Check export prerequisites."""
    state = get_app_state()

    checks = {
        'api_configured': bool(state.config.gemini_api_key),
        'credentials_exist': Path(state.config.google_docs_credentials_path).exists() if state.config.google_docs_credentials_path else False,
        'approved_items': len([i for i in state.queue.get_all_items() if i.status == ItemStatus.APPROVED]),
        'items_with_snapshots': len([i for i in state.queue.get_all_items() if i.status == ItemStatus.APPROVED and i.snapshot_path])
    }

    checks['ready'] = all([
        checks['api_configured'],
        checks['credentials_exist'],
        checks['approved_items'] > 0
    ])

    return jsonify(checks)


@app.route('/api/export/start', methods=['POST'])
def start_export():
    """Start export to Google Docs."""
    global _export_status

    if _export_status['running']:
        return jsonify({'error': 'Export already running'}), 400

    state = get_app_state()
    approved = [i for i in state.queue.get_all_items() if i.status == ItemStatus.APPROVED]

    if not approved:
        return jsonify({'error': 'No approved items'}), 400

    _export_status = {
        'running': True,
        'progress': 0,
        'total': len(approved),
        'error': None,
        'doc_url': None
    }

    thread = threading.Thread(target=_run_export, args=(approved,))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'total': len(approved)})


def _run_export(items: List[InspectionItem]):
    """Background export function."""
    global _export_status

    state = get_app_state()

    try:
        from services.google_docs_service.auth_manager import GoogleAuthManager
        from services.google_docs_service.doc_generator import GoogleDocGenerator
        from services.google_docs_service.image_uploader import GoogleImageUploader

        # Authenticate
        auth = GoogleAuthManager(state.config.google_docs_credentials_path)
        creds = auth.get_credentials()

        # Create doc generator
        generator = GoogleDocGenerator(creds)
        uploader = GoogleImageUploader(creds)

        # Generate report
        title = f"Inspection Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        doc_url = generator.create_report(title, items, uploader)

        _export_status['doc_url'] = doc_url

        # Mark items as exported
        for item in items:
            item.status = ItemStatus.EXPORTED
            item.exported_at = datetime.now()
            item.google_doc_url = doc_url
            state.queue.update_item(item)

        _export_status['progress'] = len(items)

    except Exception as e:
        _export_status['error'] = str(e)

    _export_status['running'] = False


# ============================================================================
# SETTINGS API ENDPOINTS
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings."""
    state = get_app_state()
    config = state.config

    return jsonify({
        'gemini_api_key': config.gemini_api_key[:10] + '...' if config.gemini_api_key else '',
        'google_docs_credentials_path': config.google_docs_credentials_path,
        'output_directory': config.output_directory,
        'code_folders': [{'name': f.name, 'path': f.path} for f in config.code_folders],
        'ai_settings': {
            'model_name': config.ai_settings.model_name,
            'thinking_level': config.ai_settings.thinking_level,
            'max_retries': config.ai_settings.max_retries
        },
        'pdf_settings': {
            'render_dpi': config.pdf_settings.render_dpi,
            'snapshot_dpi': config.pdf_settings.snapshot_dpi
        }
    })


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save settings."""
    data = request.json
    state = get_app_state()

    try:
        if 'gemini_api_key' in data and data['gemini_api_key']:
            state.config.gemini_api_key = data['gemini_api_key']

        if 'google_docs_credentials_path' in data:
            state.config.google_docs_credentials_path = data['google_docs_credentials_path']

        if 'output_directory' in data:
            state.config.output_directory = data['output_directory']

        if 'code_folders' in data:
            state.config.code_folders = [
                CodeFolder(name=f['name'], path=f['path'])
                for f in data['code_folders']
            ]

        if 'ai_settings' in data:
            for key, value in data['ai_settings'].items():
                if hasattr(state.config.ai_settings, key):
                    setattr(state.config.ai_settings, key, value)

        if 'pdf_settings' in data:
            for key, value in data['pdf_settings'].items():
                if hasattr(state.config.pdf_settings, key):
                    setattr(state.config.pdf_settings, key, value)

        # Save to file
        state.config_manager.save_config(state.config)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/add-folder', methods=['POST'])
def add_code_folder():
    """Add a new code folder."""
    data = request.json
    name = data.get('name')
    path = data.get('path')

    if not name or not path:
        return jsonify({'error': 'Name and path required'}), 400

    state = get_app_state()

    # Check for duplicates
    for f in state.config.code_folders:
        if f.name == name:
            return jsonify({'error': 'Folder name already exists'}), 400

    state.config.code_folders.append(CodeFolder(name=name, path=path))
    state.config_manager.save_config(state.config)

    return jsonify({'success': True})


@app.route('/api/settings/remove-folder', methods=['POST'])
def remove_code_folder():
    """Remove a code folder."""
    data = request.json
    name = data.get('name')

    state = get_app_state()
    state.config.code_folders = [f for f in state.config.code_folders if f.name != name]
    state.config_manager.save_config(state.config)

    return jsonify({'success': True})


# ============================================================================
# FILE BROWSER API
# ============================================================================

@app.route('/api/browse/folders')
def browse_folders():
    """Browse folders starting from a path."""
    start_path = request.args.get('path', str(Path.home()))

    path = Path(start_path)
    if not path.exists():
        path = Path.home()

    items = []

    # Add parent
    if path.parent != path:
        items.append({
            'name': '..',
            'path': str(path.parent),
            'is_dir': True
        })

    try:
        for item in sorted(path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'is_dir': True
                })
    except PermissionError:
        pass

    return jsonify({
        'current': str(path),
        'items': items
    })


@app.route('/api/browse/files')
def browse_files():
    """Browse files in a folder."""
    folder_path = request.args.get('path', str(Path.home()))
    extensions = request.args.get('extensions', '.jpg,.jpeg,.png,.gif,.bmp,.webp')

    path = Path(folder_path)
    if not path.exists():
        return jsonify({'error': 'Path not found'}), 404

    ext_set = set(extensions.lower().split(','))

    items = []

    # Add parent folder
    if path.parent != path:
        items.append({
            'name': '..',
            'path': str(path.parent),
            'is_dir': True
        })

    try:
        for item in sorted(path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                items.append({
                    'name': item.name + '/',
                    'path': str(item),
                    'is_dir': True
                })
            elif item.is_file() and item.suffix.lower() in ext_set:
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'is_dir': False
                })
    except PermissionError:
        pass

    return jsonify({
        'current': str(path),
        'items': items
    })


# ============================================================================
# SERVE IMAGE FILES
# ============================================================================

@app.route('/api/image/<path:image_path>')
def serve_image(image_path):
    """Serve an image file."""
    # Decode the path
    full_path = '/' + image_path

    if not Path(full_path).exists():
        return jsonify({'error': 'Image not found'}), 404

    return send_file(full_path)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import webbrowser

    url = "http://127.0.0.1:8080"

    print("=" * 50)
    print("  Inspection Photo Review")
    print("=" * 50)
    print(f"  Opening {url}")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    # Open browser after short delay (gives server time to start)
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)

    # Only open browser on first run (not on reload)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host='127.0.0.1', port=8080, debug=True)
