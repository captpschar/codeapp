"""
PDF text extraction for AI grounding.
Extracts text from PDFs so AI can search for actual code references.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF

# Gemini 2.5 Flash has ~1M token context (~4M chars), but we want to leave room for:
# - System prompt, user prompt, image data, response generation
# Single PDF limit - more generous since it's just one document
SINGLE_PDF_MAX_CHARS = 600000

# When combining multiple PDFs, use slightly lower limit
MULTI_PDF_MAX_CHARS = 500000


def get_pdf_text_size(pdf_path: str) -> Tuple[int, int]:
    """
    Scan a PDF to get its text size.

    Returns:
        Tuple of (char_count, page_count)
    """
    path = Path(pdf_path)
    if not path.exists():
        return 0, 0

    try:
        doc = fitz.open(pdf_path)
        total_chars = 0
        page_count = len(doc)

        for page in doc:
            text = page.get_text()
            total_chars += len(text)

        doc.close()
        return total_chars, page_count

    except Exception as e:
        print(f"[PDF Extract] Error scanning {pdf_path}: {e}")
        return 0, 0


def scan_pdfs_for_sizing(pdf_paths: List[str]) -> Dict:
    """
    Scan all PDFs to determine sizes and extraction strategy.

    Returns:
        Dict with sizing info and recommended strategy
    """
    results = {
        'pdfs': [],
        'total_chars': 0,
        'total_pages': 0,
        'strategy': 'single_pass',  # or 'multi_pass'
        'fits_single_pass': True
    }

    for pdf_path in pdf_paths:
        path = Path(pdf_path)
        if not path.exists():
            continue

        chars, pages = get_pdf_text_size(pdf_path)
        results['pdfs'].append({
            'path': pdf_path,
            'name': path.name,
            'chars': chars,
            'pages': pages
        })
        results['total_chars'] += chars
        results['total_pages'] += pages

    # Determine strategy
    if len(results['pdfs']) == 1:
        # Single PDF - use generous limit
        results['fits_single_pass'] = results['total_chars'] <= SINGLE_PDF_MAX_CHARS
    else:
        # Multiple PDFs - check if they all fit together
        results['fits_single_pass'] = results['total_chars'] <= MULTI_PDF_MAX_CHARS

    if not results['fits_single_pass']:
        results['strategy'] = 'multi_pass'

    return results


def extract_pdf_text_full(pdf_path: str) -> str:
    """
    Extract ALL text from a PDF file - no limits.
    """
    path = Path(pdf_path)
    if not path.exists():
        return ""

    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()
        return "\n\n".join(text_parts)

    except Exception as e:
        print(f"[PDF Extract] Error extracting {pdf_path}: {e}")
        return ""


def extract_single_pdf(pdf_path: str) -> Tuple[str, Dict]:
    """
    Extract text from a single PDF with full content.

    Returns:
        Tuple of (extracted_text, pdf_info)
    """
    path = Path(pdf_path)
    chars, pages = get_pdf_text_size(pdf_path)

    pdf_info = {
        'path': pdf_path,
        'name': path.name,
        'chars': chars,
        'pages': pages,
        'truncated': False
    }

    text = extract_pdf_text_full(pdf_path)

    # Only truncate if single PDF exceeds generous single-doc limit
    if len(text) > SINGLE_PDF_MAX_CHARS:
        text = text[:SINGLE_PDF_MAX_CHARS] + f"\n\n[... TRUNCATED - showing {SINGLE_PDF_MAX_CHARS:,} of {len(text):,} chars ...]"
        pdf_info['truncated'] = True
        print(f"[PDF Extract] ⚠ {path.name}: truncated to {SINGLE_PDF_MAX_CHARS:,} chars")
    else:
        print(f"[PDF Extract] ✓ {path.name}: {len(text):,} chars (complete)")

    header = f"\n{'='*60}\nDOCUMENT: {path.name} ({pages} pages)\n{'='*60}\n"
    return header + text, pdf_info


def extract_multiple_pdfs_smart(pdf_paths: List[str]) -> Tuple[str, Dict]:
    """
    Smart extraction that returns text and sizing info.

    Returns:
        Tuple of (combined_text, sizing_info)
    """
    if not pdf_paths:
        return "", {'strategy': 'none', 'pdfs': []}

    # Scan all PDFs first
    print(f"[PDF Extract] Scanning {len(pdf_paths)} PDF(s) for sizing...")
    sizing = scan_pdfs_for_sizing(pdf_paths)

    print(f"[PDF Extract] Total content: {sizing['total_chars']:,} chars across {sizing['total_pages']} pages")
    print(f"[PDF Extract] Strategy: {sizing['strategy']}")

    if sizing['total_chars'] == 0:
        print("[PDF Extract] WARNING: No text found in PDFs")
        return "", sizing

    all_text = []

    if sizing['fits_single_pass']:
        # Everything fits - extract all
        print(f"[PDF Extract] All content fits - extracting full documents")
        for pdf_info in sizing['pdfs']:
            text, _ = extract_single_pdf(pdf_info['path'])
            all_text.append(text)
    else:
        # Too large for single pass - will need multi-pass processing
        # For now, just return info about what's needed
        print(f"[PDF Extract] Content exceeds limit - multi-pass processing recommended")
        # Don't extract here - let the caller handle multi-pass

    result = "\n".join(all_text)
    sizing['extracted_chars'] = len(result)
    return result, sizing


# Backwards compatible function
def extract_multiple_pdfs(pdf_paths: List[str], max_total_chars: int = None) -> str:
    """Extract text from multiple PDFs."""
    text, _ = extract_multiple_pdfs_smart(pdf_paths)
    return text


def find_reference_in_pdf(pdf_path: str, reference: str) -> bool:
    """Verify that a code reference exists in the PDF."""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            if page.search_for(reference):
                doc.close()
                return True
        doc.close()
        return False
    except Exception:
        return False


def find_reference_in_multiple_pdfs(pdf_paths: List[str], reference: str) -> Optional[str]:
    """Find which PDF contains a reference."""
    for pdf_path in pdf_paths:
        if find_reference_in_pdf(pdf_path, reference):
            return pdf_path
    return None


def get_pdf_info(pdf_path: str) -> Dict:
    """Get information about a PDF file."""
    path = Path(pdf_path)
    if not path.exists():
        return {"exists": False}

    try:
        chars, pages = get_pdf_text_size(pdf_path)
        return {
            "exists": True,
            "pages": pages,
            "chars": chars,
            "filename": path.name,
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}
