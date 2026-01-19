"""
PDF text extraction for AI grounding.
Extracts text from PDFs so AI can search for actual code references.
"""

from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: str, max_pages: int = 50) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to extract (to avoid huge contexts)

    Returns:
        Extracted text content
    """
    path = Path(pdf_path)
    if not path.exists():
        return ""

    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()
        return "\n\n".join(text_parts)

    except Exception as e:
        print(f"[PDF Extract] Error extracting {pdf_path}: {e}")
        return ""


def extract_multiple_pdfs(pdf_paths: List[str], max_total_chars: int = 100000) -> str:
    """
    Extract text from multiple PDFs, combining into one context.

    Args:
        pdf_paths: List of PDF file paths
        max_total_chars: Maximum total characters to include

    Returns:
        Combined text from all PDFs
    """
    all_text = []
    total_chars = 0

    for pdf_path in pdf_paths:
        if total_chars >= max_total_chars:
            break

        path = Path(pdf_path)
        if not path.exists():
            continue

        text = extract_pdf_text(pdf_path)
        if text:
            header = f"\n{'='*60}\nDOCUMENT: {path.name}\n{'='*60}\n"
            remaining = max_total_chars - total_chars

            if len(text) > remaining:
                text = text[:remaining] + "\n[... truncated ...]"

            all_text.append(header + text)
            total_chars += len(header) + len(text)

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
