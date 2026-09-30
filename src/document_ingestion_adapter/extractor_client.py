import os

import httpx

from document_ingestion_adapter.exceptions import (
    ExtractorServiceRejectedError,
    ExtractorServiceUnavailableError,
)

EXTRACTOR_SERVICE_URL = os.getenv(
    "EXTRACTOR_SERVICE_URL",
    "http://127.0.0.1:8000",
)

EXTRACTOR_TIMEOUT_SECONDS = 60.0


async def extract_invoice_from_text(
    text: str,
    client: httpx.AsyncClient | None = None,
) -> dict:
    owns_client = False

    if client is None:
        client = httpx.AsyncClient(
            base_url=EXTRACTOR_SERVICE_URL,
            timeout=EXTRACTOR_TIMEOUT_SECONDS,
        )

        owns_client = True

    try:
        try:
            response = await client.post(
                "/extract/invoice",
                json={
                    "text": text,
                },
            )

        except httpx.RequestError as error:
            raise ExtractorServiceUnavailableError(
                "Structured Output Extractor "
                "could not be reached"
            ) from error

        if response.status_code == 422:
            try:
                response_data = response.json()

                detail = response_data.get(
                    "detail",
                    "Invoice could not be trusted",
                )

            except ValueError:
                detail = (
                    "Invoice could not be trusted"
                )

            raise ExtractorServiceRejectedError(
                detail
            )

        if response.is_error:
            raise ExtractorServiceUnavailableError(
                "Structured Output Extractor "
                f"returned HTTP "
                f"{response.status_code}"
            )

        try:
            invoice = response.json()

        except ValueError as error:
            raise ExtractorServiceUnavailableError(
                "Structured Output Extractor "
                "returned invalid JSON"
            ) from error

        if not isinstance(
            invoice,
            dict,
        ):
            raise ExtractorServiceUnavailableError(
                "Structured Output Extractor "
                "returned an invalid response"
            )

        return invoice

    finally:
        if owns_client:
            await client.aclose()