import pymupdf

from document_ingestion_adapter.ingestion import (
    ingest_document_bytes,
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


def test_native_pdf_uses_native_extraction(
    monkeypatch,
):
    pdf_bytes = build_pdf_bytes(
        "Invoice No: INV-001"
    )

    def fail_if_vision_is_called(
        images,
    ):
        raise AssertionError(
            "Vision should not be called"
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "ingestion.transcribe_images"
        ),
        fail_if_vision_is_called,
    )

    result = ingest_document_bytes(
        file_bytes=pdf_bytes,
        filename="invoice.pdf",
        content_type="application/pdf",
    )

    assert (
        result.extraction_method
        == "native_pdf_text"
    )

    assert (
        "INV-001"
        in result.text
    )


def test_scanned_pdf_falls_back_to_vision(
    monkeypatch,
):
    pdf_bytes = build_pdf_bytes(
        ""
    )

    def fake_transcribe_images(
        images,
    ):
        assert len(images) == 1

        return (
            "Invoice No: INV-SCAN-001"
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "ingestion.transcribe_images"
        ),
        fake_transcribe_images,
    )

    result = ingest_document_bytes(
        file_bytes=pdf_bytes,
        filename="scan.pdf",
        content_type="application/pdf",
    )

    assert (
        result.extraction_method
        == "vision_pdf"
    )

    assert (
        result.text
        == "Invoice No: INV-SCAN-001"
    )


def test_image_uses_vision(
    monkeypatch,
):
    def fake_transcribe_images(
        images,
    ):
        assert len(images) == 1

        return (
            "Invoice No: INV-IMG-001"
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "ingestion.transcribe_images"
        ),
        fake_transcribe_images,
    )

    result = ingest_document_bytes(
        file_bytes=b"fake-image",
        filename="invoice.png",
        content_type="image/png",
    )

    assert (
        result.extraction_method
        == "vision_image"
    )

    assert (
        result.text
        == "Invoice No: INV-IMG-001"
    )