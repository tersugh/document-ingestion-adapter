from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
)


class DocumentText(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    filename: str
    content_type: str
    extraction_method: str
    text: str
    character_count: int


class IngestionMetadata(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    filename: str
    content_type: str
    extraction_method: str
    character_count: int


class InvoiceProcessingResult(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    ingestion: IngestionMetadata

    invoice: dict[str, Any]