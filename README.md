<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/snappy_dark_nobg_resized.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/snappy_light_nobg_resized.png">
  <img width="600" alt="Snappy Logo" src="assets/snappy_light_nobg_resized.png">
</picture>

<br/>

[![arXiv](https://img.shields.io/badge/arXiv-2512.02660-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2512.02660)


[![Release](https://img.shields.io/github/v/release/athrael-soju/Snappy?include_prereleases&sort=semver&display_name=tag&style=flat-square&logo=github&color=blue)](https://github.com/athrael-soju/Snappy/releases)
[![Stars](https://img.shields.io/github/stars/athrael-soju/Snappy?style=flat-square&logo=github&color=yellow)](https://github.com/athrael-soju/Snappy/stargazers)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/athrael-soju/Snappy/release-please.yml?style=flat-square&logo=githubactions&label=build)](https://github.com/athrael-soju/Snappy/actions)

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript_5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

</div>

# Snappy - Spatially-Grounded Document Retrieval via Patch-to-Region Relevance Propagation

> **Read the Full Paper on arxiv.org**: [Spatially-Grounded Document Retrieval via Patch-to-Region Relevance Propagation](https://arxiv.org/abs/2512.02660)

Snappy implements **region-level document retrieval** by unifying vision-language models with OCR through spatial coordinate mapping. Unlike traditional systems that return entire pages (VLMs) or lack semantic grounding (OCR-only), Snappy uses ColPali's patch-level similarity scores as spatial relevance filters over OCR-extracted regions; operating entirely at inference time without additional training.

## Motivation

Vision-language models like ColPali achieve state-of-the-art document retrieval by embedding pages as images with fine-grained patch representations. However, they return **entire pages** as retrieval units, introducing irrelevant content into RAG context windows. Conversely, OCR systems extract structured text with bounding boxes but cannot assess **which regions are relevant** to a query.

Snappy bridges these paradigms through **patch-to-region relevance propagation**. The approach formalizes coordinate mapping between vision transformer patch grids (32×32) and OCR bounding boxes, repurposing ColPali's late interaction mechanism to generate interpretability maps. Patch similarity scores propagate to OCR regions via IoU-weighted intersection, enabling two-stage retrieval: efficient candidate retrieval using mean-pooled embeddings, followed by full-resolution region reranking.

This yields region-level granularity (return specific paragraphs, tables, or figures instead of entire pages), operates purely at inference time (no additional training), provides spatial interpretability (visual heatmaps showing which document regions match query tokens), and combines VLM semantic understanding with OCR structural precision in a production-ready system.



## Demo 🎬

<div align="center">

https://github.com/user-attachments/assets/95b37778-8dc3-4633-b4b2-639fc5017470

</div>


## Quick start

Prerequisites: Docker with Compose.

**1. Copy envs and set the essentials**
```bash
cp .env.example .env
```
Set `OPENAI_API_KEY` (required for chat). Other defaults are ready for local use.

**2. Start services**
```bash
docker compose up -d
```

**3. Open the UI**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs (OpenAPI)

## Architecture

<div align="center">

![architecture](https://github.com/user-attachments/assets/856228fa-53e9-48d7-9452-0231cf3905a6)
</div>

## Configuration

| Feature | When to enable | How |
|---------|----------------|-----|
| DeepSeek OCR | Need extracted text, markdown, or bounding boxes alongside visual retrieval; have an NVIDIA GPU. OCR data is stored in Qdrant payloads (~8-9 KB per page). | Set `DEEPSEEK_OCR_ENABLED=true` in `.env`. |
| Mean pooling re-ranking | Improve search accuracy with two-stage retrieval (prefetch + re-rank). More accurate but requires more compute. | Set `QDRANT_MEAN_POOLING_ENABLED=true` in `.env`. Requires ColPali model with `/patches` support (enabled in `colmodernvbert`). |
| Interpretability maps | Visualize which document regions contribute to query matches. Useful for understanding and debugging retrieval behavior. | Available in the lightbox after search. Upload a document image and query to see token-level similarity heatmaps at `/api/interpretability`. |
| Region-level retrieval | Filter OCR regions by query relevance, reducing noise and improving precision. Uses interpretability maps to return only relevant regions. | Set `ENABLE_REGION_LEVEL_RETRIEVAL=true` in Configuration UI or `.env`. Adjust `REGION_RELEVANCE_THRESHOLD` (default 0.3) to control filtering sensitivity. |
| Binary quantization | Large collections and tight RAM/GPU budget (32x memory reduction). | Enabled by default. Toggle in `.env` if needed. |

## Troubleshooting
- Progress stuck on upload/indexing: ensure Poppler is installed for PDF rasterization and check backend logs.
- Missing images: confirm `LOCAL_STORAGE_PATH` is accessible and check allowed domains in `frontend/next.config.ts`.
- Files lost after restart: ensure the `snappy_storage` Docker volume is properly mounted (configured by default in `docker-compose.yml`).
- OCR not running: ensure `DEEPSEEK_OCR_ENABLED=true` and `/ocr/health` reachable.
- Config not sticking: `/config/update` is runtime-only; edit `.env` for persistence.

## Documentation

**Core concepts** — [Late Interaction](backend/docs/late_interaction.md) explains multi-vector retrieval, MaxSim scoring, and two-stage search. [Spatial Grounding](backend/docs/spatial_grounding.md) covers how spatial information flows from pixels to regions. [Analysis](backend/docs/analysis.md) discusses when to use vision vs text RAG.

**System internals** — [Streaming Pipeline](STREAMING_PIPELINE.md) details how the indexer overlaps stages. [Architecture](backend/docs/architecture.md) provides deeper component and flow descriptions. [Configuration](backend/docs/configuration.md) is the full config reference.

**Development** — Service-specific guides are in [frontend/README.md](frontend/README.md) and [backend/README.md](backend/README.md). See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=athrael-soju/Snappy&type=Date)](https://star-history.com/#athrael-soju/Snappy&Date)

</div>

## License

[MIT](LICENSE)
