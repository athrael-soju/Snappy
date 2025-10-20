> **Rebrand Notice (2025-10-20):** This project has been rebranded from **Snappy** to **Morty™** as part of a **pro-bono** promotional collaboration with Vultr. Morty is **based on** the original Snappy project and remains compatible with existing Snappy documentation where applicable. Learn more about Snappy here: https://github.com/athrael-soju/Snappy.  
> _Morty™ is a trademark of Vultr.com. All other trademarks are the property of their respective owners._

# Morty™ Architecture – How It Fits Together

Morty keeps the same proven architecture introduced by Snappy while adopting the updated brand identity. A FastAPI backend coordinates ingestion and retrieval, a Next.js frontend handles user interactions, and supporting services deliver vector search and storage.

## High-Level Flow

1. Users upload PDFs or trigger searches from the Morty frontend.  
2. The FastAPI backend orchestrates rasterization, embedding via ColPali, and storage in Qdrant and MinIO.  
3. Retrieval requests query Qdrant, assemble citations, and stream annotated responses back to the browser through the chat API route.

## Core Services

- **Frontend (Next.js 15):** Provides the chat, upload, search, configuration, and maintenance pages. Server components stream updates to clients.  
- **Backend (FastAPI):** Exposes REST endpoints for ingestion, search, system status, and configuration. Background tasks manage long-running jobs.  
- **Qdrant:** Stores per-page multivector embeddings. Optional binary quantization improves performance on constrained hardware.  
- **MinIO:** Hosts rendered page images and static assets. Morty assumes object storage availability in all environments.  
- **ColPali API:** Generates the visual embeddings that power search and retrieval quality. CPU and GPU profiles are supported.  
- **OpenAI Responses API:** Produces grounded answers and citations in the chat workflow.

## Data Pipeline

1. **Ingestion:** Morty rasterizes PDFs with Poppler, sends images to ColPali, and persists embeddings to Qdrant. Page images land in MinIO.  
2. **Index Maintenance:** Utilities handle initialization, tear-down, and targeted cleanup for either service.  
3. **Retrieval:** Search queries run against Qdrant; results are sorted by similarity, augmented with metadata, and passed back to the frontend.  
4. **Chat Experience:** The frontend merges streamed responses with citation events to emphasize visual grounding.

## Reliability Considerations

- **Health Checks:** `GET /health` confirms connectivity to Qdrant, MinIO, and ColPali.  
- **Progress Tracking:** Server-Sent Events keep the UI informed during long ingestions.  
- **Configuration Drift:** Runtime overrides are cached, validated, and resettable without restarts.  
- **Scalability:** Morty inherits Snappy’s guidance for scaling background workers, CPU allocations, and vector storage sharding.

## Deployment Topologies

- **All-in-one docker compose:** Ideal for demos and evaluations.  
- **Managed services:** Point Morty at managed Qdrant or object storage by adjusting environment variables.  
- **Hybrid GPU:** Run the ColPali GPU service externally while keeping the rest local or containerized.

## Compatibility Notes

- Endpoint names, payloads, and response shapes are unchanged from Snappy.  
- CLI commands, make targets, and scripts retain their original names to prevent friction.  
- Morty documentation clarifies branding differences while pointing back to the upstream repository for code heritage.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
