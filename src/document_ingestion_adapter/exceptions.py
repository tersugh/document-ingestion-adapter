class DocumentIngestionError(Exception):
    """Raised when a document cannot be safely ingested."""


class ExtractorServiceError(Exception):
    """Base error for failures involving the extractor service."""


class ExtractorServiceRejectedError(
    ExtractorServiceError
):
    """
    Raised when the extractor receives the document
    but cannot produce a trusted invoice.
    """


class ExtractorServiceUnavailableError(
    ExtractorServiceError
):
    """
    Raised when the extractor service cannot be reached
    or returns an unexpected service failure.
    """