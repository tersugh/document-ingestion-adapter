from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
)
from document_ingestion_adapter.models import (
    DocumentText,
)
from document_ingestion_adapter.pdf_ingestion import (
    extract_native_text_from_pdf,
    render_pdf_pages_to_png,
)
from document_ingestion_adapter.vision import (
    transcribe_images,
)

PDF_CONTENT_TYPE = "application/pdf"

IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

ALLOWED_CONTENT_TYPES = (
    {
        PDF_CONTENT_TYPE,
    }
    | IMAGE_CONTENT_TYPES
)


def ingest_document_bytes(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> DocumentText:
    if not file_bytes:
        raise DocumentIngestionError(
            "Document is empty"
        )

    if content_type == PDF_CONTENT_TYPE:
        return ingest_pdf(
            file_bytes=file_bytes,
            filename=filename,
        )

    if content_type in IMAGE_CONTENT_TYPES:
        return ingest_image(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )

    raise DocumentIngestionError(
        "Unsupported content type"
    )


def ingest_pdf(
    file_bytes: bytes,
    filename: str,
) -> DocumentText:
    native_text = (
        extract_native_text_from_pdf(
            file_bytes
        )
    )

    if native_text:
        return DocumentText(
            filename=filename,
            content_type=PDF_CONTENT_TYPE,
            extraction_method=(
                "native_pdf_text"
            ),
            text=native_text,
            character_count=len(
                native_text
            ),
        )

    page_images = (
        render_pdf_pages_to_png(
            file_bytes
        )
    )

    vision_images = [
        (
            page_image,
            "image/png",
        )
        for page_image in page_images
    ]

    vision_text = transcribe_images(
        vision_images
    )

    return DocumentText(
        filename=filename,
        content_type=PDF_CONTENT_TYPE,
        extraction_method=(
            "vision_pdf"
        ),
        text=vision_text,
        character_count=len(
            vision_text
        ),
    )


def ingest_image(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> DocumentText:
    vision_text = transcribe_images(
        [
            (
                file_bytes,
                content_type,
            )
        ]
    )

    return DocumentText(
        filename=filename,
        content_type=content_type,
        extraction_method=(
            "vision_image"
        ),
        text=vision_text,
        character_count=len(
            vision_text
        ),
    )