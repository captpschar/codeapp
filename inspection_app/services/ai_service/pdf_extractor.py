"""
PDF text extraction for AI grounding.
Extracts text from PDFs so AI can search for actual code references.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF

# Gemini 2.5 Flash has ~1M token context (~4M chars), but we want to leave room for:
# - System prompt
# - User prompt
# - Image data
# - Response generation
# So we cap at 800k chars to be safe
ABSOLUTE_MAX_CHARS = 800000


def get_pdf_text_size(pdf_path: str) -> Tuple[int, int]:
    """
    Quickly scan a PDF to get its text size without full extraction.

    Returns:
        Tuple of (estimated_chars, page_count)
    """
    path = Path(pdf_path)
    if not path.exists():
        return 0, 0

    try:
        doc = fitz.open(pdf_path)
        total_chars = 0
        page_count = len(doc)

        # Extract text from all pages to get accurate count
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
    Scan all PDFs to determine total size and plan extraction.

    Returns:
        Dict with sizing info and extraction plan
    """
    results = {
        'pdfs': [],
        'total_chars': 0,
        'total_pages': 0,
        'fits_in_context': True,
        'needs_truncation': False
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

    # Check if everything fits
    if results['total_chars'] > ABSOLUTE_MAX_CHARS:
        results['fits_in_context'] = False
        results['needs_truncation'] = True

    return results


def extract_pdf_text_full(pdf_path: str) -> str:
    """
    Extract ALL text from a PDF file - no limits.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Complete extracted text content
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


def extract_multiple_pdfs_smart(pdf_paths: List[str]) -> str:
    """
    Smart extraction that scans PDFs first and adjusts to fit all content.

    1. Scans all PDFs to determine total size
    2. If total fits in context, extracts everything
    3. If too large, extracts proportionally from each PDF

    Args:
        pdf_paths: List of PDF file paths

    Returns:
        Combined text from all PDFs
    """
    if not pdf_paths:
        return ""

    # First pass: scan to determine sizes
    print(f"[PDF Extract] Scanning {len(pdf_paths)} PDF(s) for sizing...")
    sizing = scan_pdfs_for_sizing(pdf_paths)

    print(f"[PDF Extract] Total content: {sizing['total_chars']:,} chars across {sizing['total_pages']} pages")

    if sizing['total_chars'] == 0:
        print("[PDF Extract] WARNING: No text found in PDFs")
        return ""

    # Determine extraction strategy
    all_text = []

    if sizing['fits_in_context']:
        # Everything fits! Extract it all
        print(f"[PDF Extract] All content fits in context - extracting full documents")

        for pdf_info in sizing['pdfs']:
            text = extract_pdf_text_full(pdf_info['path'])
            if text:
                header = f"\n{'='*60}\nDOCUMENT: {pdf_info['name']} ({pdf_info['pages']} pages)\n{'='*60}\n"
                all_text.append(header + text)
                print(f"[PDF Extract] ✓ {pdf_info['name']}: {len(text):,} chars (complete)")

    else:
        # Need to be smart about extraction
        print(f"[PDF Extract] WARNING: Total content ({sizing['total_chars']:,}) exceeds limit ({ABSOLUTE_MAX_CHARS:,})")
        print(f"[PDF Extract] Extracting proportionally from each PDF...")

        # Calculate proportion for each PDF
        remaining_budget = ABSOLUTE_MAX_CHARS

        for pdf_info in sizing['pdfs']:
            # Give each PDF a proportional share of the budget
            proportion = pdf_info['chars'] / sizing['total_chars']
            char_budget = int(ABSOLUTE_MAX_CHARS * proportion)

            text = extract_pdf_text_full(pdf_info['path'])

            if text:
                header = f"\n{'='*60}\nDOCUMENT: {pdf_info['name']} ({pdf_info['pages']} pages)\n{'='*60}\n"

                if len(text) > char_budget:
                    # Truncate this PDF's content
                    text = text[:char_budget] + f"\n\n[... TRUNCATED - showing {char_budget:,} of {len(text):,} chars ...]"
                    print(f"[PDF Extract] ⚠ {pdf_info['name']}: truncated to {char_budget:,} chars")
                else:
                    print(f"[PDF Extract] ✓ {pdf_info['name']}: {len(text):,} chars (complete)")

                all_text.append(header + text)

    result = "\n".join(all_text)
    print(f"[PDF Extract] Final extraction: {len(result):,} chars")
    return result


# Keep the old function name for backwards compatibility
def extract_multiple_pdfs(pdf_paths: List[str], max_total_chars: int = None) -> str:
    """
    Extract text from multiple PDFs using smart sizing.

    Args:
        pdf_paths: List of PDF file paths
        max_total_chars: Ignored - uses smart sizing instead

    Returns:
        Combined text from all PDFs
    """
    return extract_multiple_pdfs_smart(pdf_paths)


def find_reference_in_pdf(pdf_path: str, reference: str) -> bool:
    """
    Verify that a code reference actually exists in the PDF.

    Args:
        pdf_path: Path to PDF
        reference: Code reference to search for (e.g., "R703.8")

    Returns:
        True if reference found, False otherwise
    """
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
    """
    Find which PDF contains a reference.

    Returns:
        Path to PDF containing reference, or None
    """
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
