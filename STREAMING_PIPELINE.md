# Streaming Pipeline Architecture

Snappy indexes documents with a streaming pipeline so users see searchable results within seconds instead of waiting for full batches to finish.

## Why streaming
- First searchable batch in ~10 seconds; large PDFs finish 5-6x faster than the legacy batch flow.
- GPU, CPU, and I/O stay busy together instead of waiting for one another.
- Progress is streamed to the UI, and failures stop quickly to keep data consistent.

## Flow at a glance
1. Rasterize PDF pages into small batches.
2. Each batch fans out in parallel: ColPali embeddings, image storage in MinIO, optional DeepSeek OCR.
3. Upsert waits only for embeddings, generates URLs on the fly, writes vectors to Qdrant, and updates progress.
4. When DuckDB is enabled, document metadata and OCR regions are stored for deduplication and SQL analytics.
5. Progress is streamed via SSE (`/progress/stream/{job_id}`) so the UI can reflect status immediately.

## How it compares to the old batch mode
- Streaming: overlap rasterize/compute/store/OCR, show results as soon as the first batch lands.
- Batch: rasterizes everything before embedding and upserting, so the first results arrive much later.

## Failure and cancellation
- Any stage error stops the pipeline and reports the failure through the progress stream.
- Cancellation stops running work; data cleanup is manual if needed.

## Code reference
- `backend/domain/pipeline/streaming_pipeline.py` - pipeline orchestration.
- `backend/domain/pipeline/stages/*` - rasterizer, embedding, storage, OCR, and upsert stages.
- `backend/api/progress.py` - progress tracking and SSE.
