import json

import httpx
import pytest

from document_ingestion_adapter.exceptions import (
    ExtractorServiceRejectedError,
    ExtractorServiceUnavailableError,
)
from document_ingestion_adapter.extractor_client import (
    extract_invoice_from_text,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_extractor_client_returns_invoice():
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        request_data = json.loads(
            request.content
        )

        assert request.url.path == (
            "/extract/invoice"
        )

        assert request_data == {
            "text": "Invoice text"
        }

        return httpx.Response(
            status_code=200,
            json={
                "invoice_number": (
                    "INV-001"
                ),
                "currency": "USD",
                "line_items": [],
                "subtotal": 0.0,
                "tax": 0.0,
                "total": 0.0,
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        result = (
            await extract_invoice_from_text(
                "Invoice text",
                client=client,
            )
        )

    assert (
        result["invoice_number"]
        == "INV-001"
    )


@pytest.mark.anyio
async def test_extractor_rejection_is_preserved():
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=422,
            json={
                "detail": (
                    "Invoice extraction "
                    "failed after 3 attempts"
                )
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        with pytest.raises(
            ExtractorServiceRejectedError
        ) as exc_info:
            await extract_invoice_from_text(
                "Broken invoice",
                client=client,
            )

    assert (
        "failed after 3 attempts"
        in str(exc_info.value)
    )


@pytest.mark.anyio
async def test_extractor_server_error_is_rejected():
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=500,
            json={
                "detail": (
                    "Internal server error"
                )
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        with pytest.raises(
            ExtractorServiceUnavailableError
        ):
            await extract_invoice_from_text(
                "Invoice text",
                client=client,
            )