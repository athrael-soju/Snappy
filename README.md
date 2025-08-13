# ColPali (ColQwen2) Knowledgebase Retrieval Agent

A minimal PDF RAG prototype that:

- Uses a ColQwen2.5-compatible Embeddings API for image/text embeddings
- Stores vectors in Qdrant (multi-vector schema)
- Stores page images in MinIO
- Provides a Gradio chat UI with OpenAI streaming for answers

This template now uses a single storage backend (Qdrant + MinIO). The old in-memory store has been removed.

## Architecture

- `clients/`
  - `colqwen.py`: HTTP client for the ColQwen Embeddings API
  - `minio.py`: MinIO client wrapper for storing/retrieving images
  - `qdrant.py`: Qdrant client wrapper handling collection schema, indexing, and search
- `app.py`: Gradio UI, retrieval-augmented chat, and wiring
- `config.py`: Centralized configuration sourced from environment variables
- `docker-compose.yml`: Local stack with Qdrant, MinIO, and the app container

Data flow:

1) Upload PDFs in the sidebar
2) `pdf2image` converts to page images
3) `clients.qdrant.QdrantService` embeds pages via ColQwen, stores vectors in Qdrant and images in MinIO
4) Query -> embed query -> two-stage multi-vector search in Qdrant -> fetch top-k page images from MinIO
5) Optionally send text + images to OpenAI for a streamed answer in the chat

## Requirements

- Python 3.10+
- Docker (for local stack)
- External services:
  - ColQwen Embeddings API endpoint
  - Qdrant (local via docker-compose)
  - MinIO (local via docker-compose)
  - Optional: OpenAI API key for AI answers (otherwise retrieval-only)

## Quickstart (Docker Compose)

1) Create a `.env` file in the project root with at least:

```
# App
LOG_LEVEL=INFO
WORKER_THREADS=4
BATCH_SIZE=4

# ColQwen API
COLQWEN_API_BASE_URL=http://localhost:8000
COLQWEN_API_TIMEOUT=300

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents
QDRANT_SEARCH_LIMIT=20
QDRANT_PREFETCH_LIMIT=200

# MinIO
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents
MINIO_WORKERS=4
MINIO_RETRIES=2
MINIO_FAIL_FAST=False
MINIO_IMAGE_FMT=JPEG

# OpenAI (optional for AI answers)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

2) Start the stack:

```
docker compose up --build
```

- App UI: http://localhost:7860
- Qdrant: http://localhost:6333
- MinIO Console: http://localhost:9001 (user: minioadmin / pass: minioadmin)

The app container preconfigures service URLs to `qdrant` and `minio` hostnames internally; from your host browser, use `localhost`.

## Running without Docker

Install dependencies and run the app directly:

```
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Make sure Qdrant, MinIO, and the ColQwen API are reachable at the URLs in your `.env`.

## Usage

1) Open the app in your browser
2) Upload one or more PDFs in the sidebar and click "Index documents"
3) Ask questions in the chat
4) Toggle AI responses on/off in the sidebar
   - Off: retrieval-only, you see the top-k pages
   - On: the app streams an answer from OpenAI using the retrieved images as context

## Notes

- Chat UI uses Gradio's messages format (`type="messages"`) to avoid deprecation warnings.
- The app depends on a running ColQwen embeddings service; adjust `COLQWEN_API_BASE_URL` accordingly.
- Qdrant is configured with a multi-vector schema: "original", "mean_pooling_rows", and "mean_pooling_columns".
- MinIO bucket policy is set to public read by default for simplicity.

## Troubleshooting

- Cannot connect to Qdrant/MinIO: ensure docker containers are running and URLs are correct in `.env`.
- ColQwen API health check fails: verify the API server is up and reachable.
- OpenAI streaming error: set `OPENAI_API_KEY` or disable AI responses in the sidebar.

## Project Status

- Storage backend is Qdrant-only. The legacy in-memory store has been removed.
- Services layer was renamed to `clients/` to reflect the fact they call external APIs.
