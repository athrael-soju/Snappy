# Architecture

A concise view of the Vision RAG template and its main data flows.

```mermaid
---
config:
  theme: default
  layout: elk
  look: neo
---
flowchart TB
 subgraph Services["Services"]
        QS["QdrantService - clients/qdrant.py"]
        MINIO["MinioService - clients/minio.py"]
        COL["ColQwen Client - clients/colqwen.py"]
        OAI["OpenAI Client - clients/openai.py"]
  end
 subgraph External["External"]
        QD[("Qdrant")]
        MN[("MinIO Bucket")]
        CQ[("ColQwen Embedding API")]
        OA[("OpenAI API")]
  end
    U["User Browser"] <--> UI["Gradio UI - ui.py"]
    UI --> APP["App - app.py"]
    UI -- Upload PDFs --> APP
    APP -- "PDF -> page images" --> QS
    QS -- store images --> MINIO
    MINIO --> MN
    QS -- embed images --> COL
    COL --> CQ & CQ
    QS -- upsert vectors --> QD
    UI -- Ask --> APP
    APP --> QS & UI
    QS -- embed query --> COL
    QS <-- multivector search --> QD
    QS -- fetch images --> MINIO
    QS -- page images + metadata --> APP
    APP -- text + images --> OAI
    OAI --> OA
    OAI -- stream reply --> APP
```

Notes

- __Indexing__: `app.py` converts PDFs to page images. `QdrantService` stores images in MinIO, gets embeddings from the ColQwen API (including patch metadata), mean-pools rows/cols, and upserts multivectors to Qdrant.
- __Retrieval__: `QdrantService` embeds the query via ColQwen, runs multivector search on Qdrant, fetches page images from MinIO, and returns them to `app.py`. `app.py` optionally calls OpenAI with the user text + images and streams the answer back to the UI.
- The diagram intentionally omits lower-level details (e.g., prefetch limits, comparator settings) to stay readable.
