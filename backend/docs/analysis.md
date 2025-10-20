# Morty™ System Analysis – Vision vs. Text RAG

Morty builds on Snappy’s research to deliver reliable vision-first retrieval. This analysis explains why Morty favors page images, how multivector embeddings behave in production, and when to reach for traditional text-only RAG instead.

## What Makes Morty Different

- **Visual grounding:** Morty indexes rendered page images, preserving layout, handwriting, and diagrams that OCR can miss.  
- **Multivector approach:** Each page produces pooled and patch-level vectors. Qdrant’s MAX_SIM scoring surfaces relevant passages even when terminology differs.  
- **Citation-first UI:** Morty ships citation thumbnails to clients so answers remain auditable.

## Morty vs. Text-Only RAG

| Question | Morty (Vision RAG) | Text RAG |
|----------|-------------------|---------|
| Source data | Rasterized page images + MinIO artifacts | OCR text, tokens, or embeddings |
| Strengths | Handles scans, handwriting, heavy layout, brand marks | Fast indexing, low storage overhead |
| Trade-offs | Larger payloads, higher latency per query, GPU recommended for peak throughput | Susceptible to OCR errors, loses layout context |
| Best fit | Compliance reviews, invoices, forms, design-heavy PDFs, scanned archives | Cleanly digitized documents, dense text, large corpora |

Morty encourages a hybrid approach: use Morty’s visual retrieval to bootstrap high-quality hits, then fall back to text embeddings when latency or storage takes priority.

## Cost Considerations

- **Embedding time:** CPU deployments work, but GPU-backed ColPali services cut indexing time dramatically.  
- **Storage:** Expect Qdrant collections to grow faster than pure text embeddings; plan for multivector storage and MinIO buckets.  
- **Bandwidth:** Chat citations send thumbnails to clients; budget egress accordingly.  
- **Inference budgets:** Morty leaves OpenAI pricing unchanged relative to Snappy; stream responses to keep perceived latency low.

## Optimization Levers

- Enable MUVERA for two-stage retrieval when GPU resources are available.  
- Use Qdrant binary quantization for long-tail corpora with lighter relevance demands.  
- Adjust MinIO concurrency (`MINIO_WORKERS`, `MINIO_RETRIES`) once you observe throughput limits.  
- Compress preview images or limit citation counts for extremely large documents.

## Observability

- Track ingestion metrics via background task logs and SSE events.  
- Monitor Qdrant collection stats for vector count, disk usage, and payload growth.  
- Review MinIO bucket sizing to anticipate storage upgrades.  
- Surface chat latency and OpenAI token usage in the frontend analytics pipeline.

## When Text-Only Still Wins

- You already maintain high-quality OCR output.  
- Latency budgets are strict and GPU capacity is unavailable.  
- Documents rarely contain visual cues beyond plain text.

Morty and Snappy remain compatible; you can mix both strategies by orchestrating the Morty backend alongside upstream Snappy components.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
