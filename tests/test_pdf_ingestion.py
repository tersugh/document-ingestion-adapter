import pymupdf
import pytest

from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
)
from document_ingestion_adapter.pdf_ingestion import (
    extract_native_text_from_pdf,
    render_pdf_pages_to_png,
)


def build_pdf_bytes(
    text: str,
) -> bytes:
    document = pymupdf.open()

    page = document.new_page()

    if text:
        page.insert_text(
            (72, 72),
            text,
        )

    pdf_bytes = document.tobytes()

    document.close()

    return pdf_bytes


def test_extracts_native_text_from_pdf():
    pdf_bytes = build_pdf_bytes(
        "Invoice No: INV-001"
    )

    result = (
        extract_native_text_from_pdf(
            pdf_bytes
        )
    )

    assert (
        "Invoice No: INV-001"
        in result
    )


def test_empty_pdf_bytes_are_rejected():
    with pytest.raises(
        DocumentIngestionError
    ) as exc_info:
        extract_native_text_from_pdf(
            b""
        )

    assert (
        "PDF file is empty"
        in str(exc_info.value)
    )


def test_pdf_without_text_returns_empty_string():
    pdf_bytes = build_pdf_bytes(
        ""
    )

    result = (
        extract_native_text_from_pdf(
            pdf_bytes
        )
    )

    assert result == ""


def test_pdf_can_be_rendered_to_png():
    pdf_bytes = build_pdf_bytes(
        ""
    )

    images = render_pdf_pages_to_png(
        pdf_bytes
    )

    assert len(images) == 1

    assert images[0].startswith(
        b"\x89PNG"
    )