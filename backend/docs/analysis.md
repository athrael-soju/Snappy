# Snappy System Analysis - Vision vs Text RAG

Snappy is vision-first: it embeds page images with ColPali multivectors so layout, figures, and handwriting stay searchable. OCR and DuckDB are optional add-ons that improve text grounding and analytics when you need them.

## What is different about Snappy
- Multivector embeddings per page (original tokens plus pooled variants) keep layout signals.
- Two-stage search: pooled vectors prefetch, originals rerank for accuracy.
- Retrieval sends images (and optional OCR text) to the LLM for grounded answers.
- Streaming indexing overlaps rasterize, embed, storage, and OCR so first results arrive quickly.

## Choosing a mode
| Scenario | Suggested mode | Why |
|----------|----------------|-----|
| Scans, forms, tables, diagrams, handwriting | Vision-only (ColPali + images) | Layout and visual cues matter more than OCR quality. |
| Text-heavy PDFs with reliable print | Hybrid (ColPali + OCR text) | Adds searchable text and lower token costs while keeping visual grounding. |
| Need bounding boxes or region images (figures/tables) | Hybrid with OCR regions enabled | Returns text and cropped regions for the LLM. |
| Deduplication or analytics over OCR results | Hybrid with DuckDB enabled | Stores structured OCR data and document metadata for SQL and dedup checks. |
| Constrained hardware | Minimal profile (no OCR, quantization options) | Runs on CPU; fewer services. |

## Trade-offs and limits
- Vision-first costs more compute than text-only RAG but handles layout-heavy documents better.
- OCR requires an NVIDIA GPU and adds latency; disable it when you only need visual search.
- DuckDB improves analytics and inline OCR responses but adds one more service to run.
- Without OCR, very fine text may be missed; without images, layout context is lost.

## Implementation pointers
- Search and rerank: `backend/clients/qdrant/search.py`, `backend/clients/qdrant/embedding.py`.
- Indexing pipeline: `backend/domain/pipeline/streaming_pipeline.py` and stage modules.
- OCR services: `backend/clients/ocr/*`, `backend/services/ocr/*`.
- Configuration: `backend/config/schema/*` and `backend/docs/configuration.md`.
- Frontend chat flow: `frontend/app/api/chat/route.ts` (streams OpenAI responses with citations).
