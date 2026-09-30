from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
    ExtractorServiceRejectedError,
    ExtractorServiceUnavailableError,
)
from document_ingestion_adapter.extractor_client import (
    extract_invoice_from_text,
)
from document_ingestion_adapter.ingestion import (
    ALLOWED_CONTENT_TYPES,
    ingest_document_bytes,
)
from document_ingestion_adapter.models import (
    DocumentText,
    IngestionMetadata,
    InvoiceProcessingResult,
)

MAX_FILE_SIZE_BYTES = (
    10
    * 1024
    * 1024
)


app = FastAPI(
    title="Document Ingestion Adapter",
    version="0.3.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }


async def read_uploaded_document(
    file: UploadFile,
) -> tuple[
    bytes,
    str,
    str,
]:
    content_type = (
        file.content_type
        or ""
    )

    if (
        content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported file type"
            ),
        )

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file is empty"
            ),
        )

    if (
        len(file_bytes)
        > MAX_FILE_SIZE_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                "Uploaded file exceeds "
                "the 10 MB limit"
            ),
        )

    filename = (
        file.filename
        or "unknown"
    )

    return (
        file_bytes,
        filename,
        content_type,
    )


@app.post(
    "/ingest",
    response_model=DocumentText,
)
async def ingest_document(
    file: Annotated[
        UploadFile,
        File(
            description=(
                "PDF or image document "
                "to ingest"
            )
        ),
    ],
) -> DocumentText:
    (
        file_bytes,
        filename,
        content_type,
    ) = await read_uploaded_document(
        file
    )

    try:
        result = ingest_document_bytes(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )

    except DocumentIngestionError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return result


@app.post(
    "/ingest/invoice",
    response_model=InvoiceProcessingResult,
)
async def ingest_invoice(
    file: Annotated[
        UploadFile,
        File(
            description=(
                "Invoice PDF or image"
            )
        ),
    ],
) -> InvoiceProcessingResult:
    (
        file_bytes,
        filename,
        content_type,
    ) = await read_uploaded_document(
        file
    )

    try:
        document = ingest_document_bytes(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )

    except DocumentIngestionError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    try:
        invoice = (
            await extract_invoice_from_text(
                document.text
            )
        )

    except (
        ExtractorServiceRejectedError
    ) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (
        ExtractorServiceUnavailableError
    ) as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    ingestion_metadata = (
        IngestionMetadata(
            filename=document.filename,
            content_type=(
                document.content_type
            ),
            extraction_method=(
                document.extraction_method
            ),
            character_count=(
                document.character_count
            ),
        )
    )

    return InvoiceProcessingResult(
        ingestion=ingestion_metadata,
        invoice=invoice,
    )