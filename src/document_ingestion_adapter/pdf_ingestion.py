import pymupdf

from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
)


MAX_PDF_PAGES = 10
PDF_RENDER_DPI = 180


def open_pdf(
        file_bytes: bytes,
) -> pymupdf.Document:
    if not file_bytes:
        raise DocumentIngestionError(
            "PDF file is empty"
        )

    
    try: 
        document = pymupdf.open(
            stream=file_bytes,
            filetype="pdf",
        )

    except Exception as error:
        raise DocumentIngestionError(
            "PDF could not be opened"
        ) from error

    return document


def extract_native_text_from_pdf(
        file_bytes: bytes,
) -> str:
    document = open_pdf(
        file_bytes
    )

    try:
        pages = []

        for page in document:
            page_text = page.get_text(
                "text"
            ).strip()

            if page_text:
                pages.append(
                    page_text
                )

        extracted_text = "\n\n".join(
            pages
        ).strip()

    finally:
        document.close()

    return extracted_text


def render_pdf_pages_to_png(
        file_bytes: bytes,
        max_pages: int = MAX_PDF_PAGES,
) -> list[bytes]:
    document = open_pdf(
        file_bytes
    )

    try:
        if document.page_count == 0:
            raise DocumentIngestionError(
                "PDF contains no pages"
            )

        if document.page_count > max_pages:
            raise DocumentIngestionError(
                f"PDF exceeds the "
                f"{max_pages}-page limit"
            )

        page_images = []

        for page in document:
            pixmap = page.get_pixmap(
                dpi=PDF_RENDER_DPI,
                alpha=False,
            )

            png_bytes = pixmap.tobytes(
                "png"
            )

            page_images.append(
                png_bytes
            )

    finally:
        document.close()

    return page_images