"""
PDF text extraction for AI grounding.
Extracts text from PDFs so AI can search for actual code references.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: str, max_pages: int = 200) -> Tuple[str, int, int]:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to extract

    Returns:
        Tuple of (extracted text, pages extracted, total pages)
    """
    path = Path(pdf_path)
    if not path.exists():
        return "", 0, 0

    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        text_parts = []

        pages_to_extract = min(total_pages, max_pages)
        for page_num in range(pages_to_extract):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()

        extracted_text = "\n\n".join(text_parts)
        return extracted_text, pages_to_extract, total_pages

    except Exception as e:
        print(f"[PDF Extract] Error extracting {pdf_path}: {e}")
        return "", 0, 0


def extract_multiple_pdfs(pdf_paths: List[str], max_total_chars: int = 500000) -> str:
    """
    Extract text from multiple PDFs, combining into one context.

    Gemini 2.5 has 1M token context, so we can be generous with text.

    Args:
        pdf_paths: List of PDF file paths
        max_total_chars: Maximum total characters (default 500k ~ 125k tokens)

    Returns:
        Combined text from all PDFs
    """
    all_text = []
    total_chars = 0

    for pdf_path in pdf_paths:
        path = Path(pdf_path)
        if not path.exists():
            print(f"[PDF Extract] File not found: {pdf_path}")
            continue

        text, pages_extracted, total_pages = extract_pdf_text(pdf_path)

        if not text:
            print(f"[PDF Extract] No text extracted from: {path.name}")
            continue

        print(f"[PDF Extract] {path.name}: extracted {pages_extracted}/{total_pages} pages, {len(text)} chars")

        header = f"\n{'='*60}\nDOCUMENT: {path.name}\n{'='*60}\n"

        # Check if we need to truncate
        remaining = max_total_chars - total_chars
        if len(text) + len(header) > remaining:
            if remaining > 1000:  # Only include if we have meaningful space left
                text = text[:remaining - len(header) - 50] + "\n\n[... DOCUMENT TRUNCATED - content continues beyond this point ...]"
                print(f"[PDF Extract] WARNING: Truncated {path.name} to fit context limit")
            else:
                print(f"[PDF Extract] WARNING: Skipping {path.name} - context limit reached")
                continue

        all_text.append(header + text)
        total_chars += len(header) + len(text)

    if total_chars >= max_total_chars * 0.9:
        print(f"[PDF Extract] WARNING: Near context limit ({total_chars}/{max_total_chars} chars)")

    return "\n".join(all_text)


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
        doc = fitz.open(pdf_path)
        info = {
            "exists": True,
            "pages": len(doc),
            "filename": path.name,
        }

        # Estimate text size
        sample_text = ""
        for i in range(min(3, len(doc))):
            sample_text += doc[i].get_text()

        avg_chars_per_page = len(sample_text) / min(3, len(doc)) if len(doc) > 0 else 0
        info["estimated_chars"] = int(avg_chars_per_page * len(doc))

        doc.close()
        return info

    except Exception as e:
        return {"exists": True, "error": str(e)}
