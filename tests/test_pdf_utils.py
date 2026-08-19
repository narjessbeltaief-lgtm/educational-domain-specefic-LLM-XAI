"""Unit tests for src.utils.pdf_utils."""

import io

import pytest
from pypdf import PdfWriter

from src.utils.pdf_utils import PDFExtractionError, extract_text_from_pdf


def _make_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_blank_pdf_raises_extraction_error():
    with pytest.raises(PDFExtractionError):
        extract_text_from_pdf(_make_blank_pdf_bytes())


def test_invalid_pdf_bytes_raises_extraction_error():
    with pytest.raises(PDFExtractionError):
        extract_text_from_pdf(b"this is not a real pdf")
