import base64

from openai import APIError, OpenAI

from document_ingestion_adapter.exceptions import (
    DocumentIngestionError,
)

VISION_MODEL = "gpt-6-luna"

VISION_TIMEOUT_SECONDS = 60.0

VISION_TRANSPORT_RETRIES = 1


TRANSCRIPTION_INSTRUCTIONS = """
Transcribe the visible text in these document images faithfully.

Rules:
- return only the transcription
- preserve the document's wording
- preserve line order as closely as possible
- preserve numbers, currencies, dates, and identifiers
- do not summarize
- do not interpret the document
- do not correct arithmetic
- do not invent missing text
- do not rewrite spelling or grammar
- process multiple images in the order provided
"""


def image_to_data_url(
        image_bytes: bytes,
        content_type: str,
) -> str:
    if not image_bytes:
        raise DocumentIngestionError(
            "Image is empty"
        )

    encoded_image = base64.b64encode(
        image_bytes
    ).decode(
        "ascii"
    )

    return (
        f"data:{content_type};base64,"
        f"{encoded_image}"
    )

def transcribe_images(
        images: list[
            tuple[bytes, str]
        ],
        client: OpenAI | None = None,
) -> str:
    if not images:
        raise DocumentIngestionError(
            "No images were provided"
        )

    if client is None:
        client = OpenAI(
            timeout=VISION_TIMEOUT_SECONDS,
            max_retries=VISION_TRANSPORT_RETRIES,
        )

    content = [
            {
                "type": "input_text",
                "text": TRANSCRIPTION_INSTRUCTIONS,
            }
        ]

    for image_bytes, content_type in images:
        data_url = image_to_data_url(
            image_bytes,
            content_type,
        )

        content.append(
            {
                "type": "input_image",
                "image_url": data_url,
            }
        )

    try:

        response = client.responses.create(
            model=VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            store=False,
        )

    except APIError as error:
        raise DocumentIngestionError(
            "Vision transcription failed"
        ) from error 

    transcription = (
        response.output_text.strip()
    )

    if transcription == "":
        raise DocumentIngestionError(
            "Vision returned no text"
        )

    return transcription