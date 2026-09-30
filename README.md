# Document Ingestion Adapter

A multimodal document-ingestion service that accepts PDFs and images, extracts their visible text using the most appropriate strategy, and can forward that text to a separate structured-output service for deterministic business-data extraction.

This is **Project 002** in my AI engineering learning series.

It was deliberately designed as a separate service from my [Structured Output Extractor](https://github.com/tersugh/structured-output-extractor), keeping **document understanding** separate from **domain extraction and validation**.

---

## The Problem

Real business documents do not arrive as convenient strings.

They arrive as:

- digitally generated PDFs
- scanned PDFs
- screenshots
- photographs
- PNG/JPEG/WebP images

My first project, the Structured Output Extractor, already knew how to turn invoice **text** into validated structured data.

But it deliberately did not know how to:

- accept file uploads
- parse PDFs
- detect scanned documents
- process images
- perform multimodal transcription

Rather than adding all of that into the extraction engine, I built a separate ingestion adapter.

The result is a cleaner architecture:

```text
PDF / image
    ↓
Document Ingestion Adapter
    ↓
faithful document text
    ↓ HTTP
Structured Output Extractor
    ↓
validated domain JSON
```

Each service owns one responsibility.

---

# Architecture

```text
                         Uploaded Document
                                │
                                ▼
                    ┌───────────────────────┐
                    │   File Validation     │
                    │ type / size / empty   │
                    └───────────┬───────────┘
                                │
                       inspect content type
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
             PDF                                Image
              │                                   │
              ▼                                   ▼
     Native text extraction                 Vision model
          with PyMuPDF                           │
              │                                   │
       ┌──────┴──────┐                            │
       │             │                            │
   text found     no text                         │
       │             │                            │
       │             ▼                            │
       │       render PDF pages                   │
       │          as PNG                          │
       │             │                            │
       │             ▼                            │
       │        Vision model                      │
       │             │                            │
       └─────────────┴──────────────┬─────────────┘
                                    │
                                    ▼
                           DocumentText result
                                    │
                                    ▼
                    POST /extract/invoice
                                    │
                         Project 001 over HTTP
                                    │
                                    ▼
                         Validated Invoice JSON
```

---

# Supported Inputs

The service currently accepts:

```text
application/pdf
image/png
image/jpeg
image/webp
```

It automatically selects one of three ingestion strategies.

### Digital PDF

```text
PDF
↓
PyMuPDF native text extraction
↓
native_pdf_text
```

### Scanned / image-only PDF

```text
PDF
↓
native extraction returns no text
↓
render each page to PNG
↓
vision transcription
↓
vision_pdf
```

### Standalone image

```text
PNG / JPEG / WebP
↓
vision transcription
↓
vision_image
```

The caller does not need to choose the strategy manually.

---

# Core Design Principle

The ingestion service answers:

> **What does this document say?**

It does not decide:

> **What business data should be trusted from it?**

That responsibility belongs to the Structured Output Extractor.

This separation means the ingestion adapter can eventually support many document domains without becoming coupled to invoices.

For example:

```text
document ingestion
       ↓
       ├── invoice extractor
       ├── contract extractor
       ├── support-ticket extractor
       ├── receipt extractor
       └── form extractor
```

---

# Project Structure

```text
document-ingestion-adapter/
├── src/
│   └── document_ingestion_adapter/
│       ├── __init__.py
│       ├── api.py
│       ├── exceptions.py
│       ├── extractor_client.py
│       ├── ingestion.py
│       ├── models.py
│       ├── pdf_ingestion.py
│       └── vision.py
├── tests/
│   ├── test_api.py
│   ├── test_extractor_client.py
│   ├── test_ingestion.py
│   ├── test_pdf_ingestion.py
│   └── test_vision.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# Responsibilities by Module

## `pdf_ingestion.py`

Owns PDF-specific operations:

- opening PDF bytes
- extracting native text
- rendering PDF pages to PNG
- page-count limits
- PDF parsing failures

It does not call the AI model.

---

## `vision.py`

Owns multimodal transcription:

- Base64 image encoding
- image data URLs
- OpenAI vision requests
- transcription instructions
- API timeout and transport retry configuration
- vision-service failures

The vision model is instructed to transcribe faithfully rather than summarize, reinterpret, or repair the document.

---

## `ingestion.py`

The orchestration layer.

It decides which strategy should execute:

```text
PDF with text → native extraction

PDF without text → render + vision

Image → vision
```

This is intentionally separate from both HTTP handling and low-level PDF/vision implementations.

---

## `extractor_client.py`

Owns communication with Project 001.

Project 002 does not import Project 001's Python functions.

Instead, the two services communicate through HTTP:

```text
Project 002
    ↓
POST /extract/invoice
    ↓
Project 001
```

This preserves a real service boundary.

---

## `api.py`

The HTTP layer handles:

- multipart file uploads
- MIME-type validation
- maximum file size
- empty files
- request routing
- application-error translation
- HTTP responses

It does not contain PDF parsing or vision logic.

---

# API

Run the service:

```bash
uv run uvicorn \
  document_ingestion_adapter.api:app \
  --reload \
  --port 8001
```

Open:

```text
http://127.0.0.1:8001/docs
```

FastAPI generates interactive documentation automatically.

---

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

## Ingest Document

```http
POST /ingest
```

Accepts a PDF or supported image and returns faithful document text.

Example response:

```json
{
  "filename": "invoice.png",
  "content_type": "image/png",
  "extraction_method": "vision_image",
  "text": "INVOICE\nInvoice No: INV-2026-00873\n...",
  "character_count": 1499
}
```

This endpoint does **not** perform invoice extraction.

It only performs document ingestion.

---

# End-to-End Invoice Processing

```http
POST /ingest/invoice
```

This endpoint:

```text
file
↓
document ingestion
↓
text
↓
Structured Output Extractor
↓
validated invoice
```

Example response:

```json
{
  "ingestion": {
    "filename": "test_invoice.png",
    "content_type": "image/png",
    "extraction_method": "vision_image",
    "character_count": 1499
  },
  "invoice": {
    "invoice_number": "INV-2026-00873",
    "currency": "GBP",
    "line_items": [
      {
        "description": "Industrial Temperature Sensor",
        "quantity": 6,
        "unit_price": 145.0,
        "amount": 870.0
      }
    ],
    "subtotal": 2330.0,
    "tax": 466.0,
    "total": 2796.0
  }
}
```

The structured invoice returned here has already passed the deterministic validation rules implemented by Project 001.

---

# Failure Boundaries

Different failures represent different problems and are handled separately.

```text
unsupported document type
→ 415

empty upload
→ 400

document ingestion / vision failure
→ 422

downstream extractor rejects invoice
→ 422

downstream extractor unavailable / server failure
→ 502
```

This distinction became particularly useful during development.

For example, an early end-to-end request returned:

```text
502 Bad Gateway
```

Investigation showed that Project 002 had successfully contacted Project 001, but Project 001 itself returned `500` because its OpenAI credentials were missing.

The service boundary made the failure visible instead of silently hiding it.

---

# Local Development

This project uses `uv`.

Install dependencies:

```bash
uv sync
```

Create:

```text
.env
```

with:

```env
OPENAI_API_KEY=your-key-here
EXTRACTOR_SERVICE_URL=http://127.0.0.1:8000
```

Never commit `.env`.

An `.env.example` can safely contain:

```env
OPENAI_API_KEY=
EXTRACTOR_SERVICE_URL=http://127.0.0.1:8000
```

---

# Running the Full System

Project 001 must run on port `8000`.

```bash
cd ~/Development/structured-output-extractor

uv run uvicorn \
  structured_output_extractor.api:app \
  --reload \
  --port 8000
```

Then run Project 002 on port `8001`.

```bash
cd ~/Development/document-ingestion-adapter

uv run uvicorn \
  document_ingestion_adapter.api:app \
  --reload \
  --port 8001
```

The resulting architecture is:

```text
:8001
Document Ingestion Adapter
        ↓ HTTP
:8000
Structured Output Extractor
```

---

# Testing

Run:

```bash
uv run pytest -v
```

The test suite covers:

- native PDF text extraction
- blank PDFs
- PDF-to-PNG rendering
- image Base64 encoding
- vision request construction
- deterministic vision mocks
- PDF strategy selection
- scanned-PDF fallback
- standalone image routing
- file upload validation
- ingestion failures
- downstream extractor communication
- downstream validation rejection
- HTTP service failures
- end-to-end API orchestration

External AI and HTTP dependencies are mocked during unit tests so tests remain:

```text
fast
deterministic
network-independent
inexpensive
```

Real multimodal behavior was additionally tested manually with both invoice images and scanned PDFs.

---

# What I Learned

This project introduced several concepts beyond Project 001.

### Multimodal systems

The system no longer receives only text.

It now has to reason about different input representations:

```text
binary file
PDF structure
pixels
Base64
text
structured data
```

---

### Strategy selection

The system dynamically selects an execution path based on the input and intermediate results:

```text
inspect
↓
choose strategy
↓
execute
↓
inspect result
↓
fallback when necessary
```

That pattern appears frequently in larger agentic systems.

---

### Service boundaries

Rather than combining everything into one application, document ingestion and domain extraction remain independently executable services.

This introduced practical lessons around:

- HTTP clients
- asynchronous I/O
- timeouts
- downstream failures
- `502 Bad Gateway`
- configuration
- environment variables
- service contracts

---

### Dependency isolation

Tests should not require:

- real OpenAI requests
- live external services
- another local application to be running

Using fake clients, monkeypatching, and HTTP mock transports allowed each layer to be tested independently.

---

# Connection to Agentic Engineering

This project is not an autonomous agent.

But it introduces architecture that becomes increasingly important when building reliable agents.

A robust agent often needs to:

```text
inspect its environment
↓
select an appropriate tool
↓
execute the tool
↓
interpret the result
↓
use a fallback strategy when necessary
↓
communicate with other services
↓
stop safely when a dependency fails
```

The Document Ingestion Adapter performs a deterministic version of that pattern.

Combined with Project 001, the system now contains:

- multimodal input handling
- strategy routing
- tool-like components
- deterministic validation
- fallback behavior
- bounded retries
- observability
- explicit trust boundaries
- inter-service communication
- failure classification

The goal of both projects has been to understand the engineering surrounding AI models rather than treating the model call itself as the application.

---

# Current End-to-End System

```text
                    REAL-WORLD DOCUMENT
                            │
             ┌──────────────┴──────────────┐
             │                             │
            PDF                          IMAGE
             │                             │
             ▼                             ▼
       Native parser                    Vision
             │                             │
       no text? ─── yes → Vision            │
             │                             │
             └──────────────┬──────────────┘
                            ▼
                    Faithful document text
                            │
                            ▼
                  HTTP service boundary
                            │
                            ▼
                Structured Output Extractor
                            │
                            ▼
                    Structured Outputs
                            │
                            ▼
                      Pydantic models
                            │
                            ▼
                    Semantic validation
                            │
                            ▼
                    TRUSTED DOMAIN DATA
```

---

# Future Work

Possible extensions include:

- multi-document batch ingestion
- asynchronous background jobs
- persistent processing history
- page-level transcription metadata
- OCR/vision quality comparison
- evaluation datasets
- confidence and review workflows
- object storage integration
- document-type classification
- additional downstream domain extractors
- authentication and rate limiting
- distributed tracing across both services

---

# Status

**Project 002 — working end-to-end.**

Successfully tested with:

```text
digital PDF
scanned PDF
invoice image
multimodal vision fallback
service-to-service extraction
validated structured invoice output
```

Built as a hands-on exploration of multimodal pipelines, service boundaries, failure handling, and the infrastructure required around reliable AI systems.