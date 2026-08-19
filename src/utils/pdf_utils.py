"""Extract plain text from an uploaded course PDF."""

from __future__ import annotations

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFExtractionError(RuntimeError):
    """Raised when text cannot be extracted from the uploaded PDF."""


def extract_text_from_pdf(file_bytes: bytes, max_pages: int | None = None) -> str:
    """Extract and concatenate text from every page of a PDF.

    Args:
        file_bytes: raw PDF file contents
        max_pages: optional cap on number of pages to read (large decks/books)

    Returns:
        Extracted text, pages joined with double newlines.

    Raises:
        PDFExtractionError: if the file can't be parsed or contains no
            extractable text (e.g. a pure scan with no OCR layer).
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001
        raise PDFExtractionError(f"Could not read PDF: {exc}") from exc

    pages = reader.pages if max_pages is None else reader.pages[:max_pages]
    chunks = []
    for i, page in enumerate(pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to extract text from page %d: %s", i, exc)
            text = ""
        if text.strip():
            chunks.append(text.strip())

    full_text = "\n\n".join(chunks)
    if not full_text.strip():
        raise PDFExtractionError(
            "No extractable text found in PDF (it may be a scanned document "
            "without an OCR text layer)."
        )
    return full_text
