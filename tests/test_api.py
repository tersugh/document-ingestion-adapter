from fastapi.testclient import (
    TestClient,
)

from document_ingestion_adapter.api import (
    app,
)
from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
    ExtractorServiceRejectedError,
)
from document_ingestion_adapter.models import (
    DocumentText,
)

client = TestClient(app)


def build_document_result(
    filename: str,
    content_type: str,
) -> DocumentText:
    return DocumentText(
        filename=filename,
        content_type=content_type,
        extraction_method=(
            "native_pdf_text"
        ),
        text=(
            "Invoice No: INV-001"
        ),
        character_count=19,
    )


def test_health_endpoint():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
    }


def test_pdf_upload_returns_ingestion_result(
    monkeypatch,
):
    def fake_ingest_document_bytes(
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> DocumentText:
        return build_document_result(
            filename,
            content_type,
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.ingest_document_bytes"
        ),
        fake_ingest_document_bytes,
    )

    response = client.post(
        "/ingest",
        files={
            "file": (
                "invoice.pdf",
                b"fake-pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "filename"
        ]
        == "invoice.pdf"
    )


def test_image_upload_is_accepted(
    monkeypatch,
):
    def fake_ingest_document_bytes(
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> DocumentText:
        return DocumentText(
            filename=filename,
            content_type=content_type,
            extraction_method=(
                "vision_image"
            ),
            text=(
                "Invoice No: INV-IMG-001"
            ),
            character_count=23,
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.ingest_document_bytes"
        ),
        fake_ingest_document_bytes,
    )

    response = client.post(
        "/ingest",
        files={
            "file": (
                "invoice.png",
                b"fake-image",
                "image/png",
            )
        },
    )

    assert response.status_code == 200


def test_unsupported_file_type_is_rejected():
    response = client.post(
        "/ingest",
        files={
            "file": (
                "invoice.txt",
                b"hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_empty_upload_is_rejected():
    response = client.post(
        "/ingest",
        files={
            "file": (
                "invoice.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400


def test_ingestion_failure_becomes_422(
    monkeypatch,
):
    def fake_ingest_document_bytes(
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ):
        raise DocumentIngestionError(
            "Vision transcription failed"
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.ingest_document_bytes"
        ),
        fake_ingest_document_bytes,
    )

    response = client.post(
        "/ingest",
        files={
            "file": (
                "scan.pdf",
                b"fake-pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422


def test_invoice_endpoint_returns_validated_invoice(
    monkeypatch,
):
    def fake_ingest_document_bytes(
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> DocumentText:
        return build_document_result(
            filename,
            content_type,
        )

    async def fake_extract_invoice_from_text(
        text: str,
    ) -> dict:
        assert (
            text
            == "Invoice No: INV-001"
        )

        return {
            "invoice_number": "INV-001",
            "currency": "USD",
            "line_items": [],
            "subtotal": 0.0,
            "tax": 0.0,
            "total": 0.0,
        }

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.ingest_document_bytes"
        ),
        fake_ingest_document_bytes,
    )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.extract_invoice_from_text"
        ),
        fake_extract_invoice_from_text,
    )

    response = client.post(
        "/ingest/invoice",
        files={
            "file": (
                "invoice.pdf",
                b"fake-pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["ingestion"][
            "extraction_method"
        ]
        == "native_pdf_text"
    )

    assert (
        data["invoice"][
            "invoice_number"
        ]
        == "INV-001"
    )


def test_invoice_rejection_becomes_422(
    monkeypatch,
):
    def fake_ingest_document_bytes(
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> DocumentText:
        return build_document_result(
            filename,
            content_type,
        )

    async def fake_extract_invoice_from_text(
        text: str,
    ) -> dict:
        raise ExtractorServiceRejectedError(
            "Invoice could not be trusted"
        )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.ingest_document_bytes"
        ),
        fake_ingest_document_bytes,
    )

    monkeypatch.setattr(
        (
            "document_ingestion_adapter."
            "api.extract_invoice_from_text"
        ),
        fake_extract_invoice_from_text,
    )

    response = client.post(
        "/ingest/invoice",
        files={
            "file": (
                "invoice.pdf",
                b"fake-pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422