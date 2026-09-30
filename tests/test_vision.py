from document_ingestion_adapter.vision import (
    image_to_data_url,
    transcribe_images,
)


class FakeResponse:
    output_text = (
        "Invoice No: INV-001"
    )


class FakeResponses:
    def __init__(self):
        self.last_request = None

    def create(
        self,
        **kwargs,
    ):
        self.last_request = kwargs

        return FakeResponse()


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_image_is_encoded_as_data_url():
    result = image_to_data_url(
        b"fake-image-bytes",
        "image/png",
    )

    assert result.startswith(
        "data:image/png;base64,"
    )


def test_vision_transcription_uses_image_input():
    client = FakeOpenAIClient()

    result = transcribe_images(
        [
            (
                b"fake-image-bytes",
                "image/png",
            )
        ],
        client=client,
    )

    assert result == (
        "Invoice No: INV-001"
    )

    request = (
        client.responses.last_request
    )

    content = (
        request["input"][0]["content"]
    )

    assert (
        content[0]["type"]
        == "input_text"
    )

    assert (
        content[1]["type"]
        == "input_image"
    )

    assert content[1][
        "image_url"
    ].startswith(
        "data:image/png;base64,"
    )