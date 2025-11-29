<p align="center">
  <img width="754" height="643" alt="Snappy_light_readme" src="https://github.com/user-attachments/assets/1da5d693-2b1b-483b-8c50-88c53aae3b59" />
</p>

<p align="center">
  <!-- Project Stats -->
  <a href="https://github.com/athrael-soju/Snappy/releases"><img src="https://img.shields.io/github/v/release/athrael-soju/Snappy?include_prereleases&sort=semver&display_name=tag&style=flat-square&logo=github&color=blue" alt="GitHub Release"></a>
  <a href="https://github.com/athrael-soju/Snappy/stargazers"><img src="https://img.shields.io/github/stars/athrael-soju/Snappy?style=flat-square&logo=github&color=yellow" alt="GitHub Stars"></a>
  <a href="https://github.com/athrael-soju/Snappy/network/members"><img src="https://img.shields.io/github/forks/athrael-soju/Snappy?style=flat-square&logo=github&color=green" alt="GitHub Forks"></a>
  <a href="https://github.com/athrael-soju/Snappy/issues"><img src="https://img.shields.io/github/issues/athrael-soju/Snappy?style=flat-square&logo=github&color=red" alt="GitHub Issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
</p>

<p align="center">
  <!-- Build & Quality -->
  <a href="https://github.com/athrael-soju/Snappy/actions"><img src="https://img.shields.io/github/actions/workflow/status/athrael-soju/Snappy/release-please.yml?style=flat-square&logo=githubactions&label=CI%2FCD" alt="CI/CD"></a>
  <a href="https://github.com/athrael-soju/Snappy/security/code-scanning"><img src="https://img.shields.io/github/actions/workflow/status/athrael-soju/Snappy/codeql.yml?style=flat-square&logo=github&label=CodeQL" alt="CodeQL"></a>
  <a href="https://github.com/athrael-soju/Snappy"><img src="https://img.shields.io/badge/code%20quality-A+-brightgreen?style=flat-square&logo=codacy" alt="Code Quality"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square&logo=pre-commit" alt="Pre-commit"></a>
</p>

<p align="center">
  <!-- Tech Stack -->
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Frontend-Next.js%2016-000000?style=flat-square&logo=next.js" alt="Next.js"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react" alt="React"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"></a>
  <a href="https://qdrant.tech/"><img src="https://img.shields.io/badge/VectorDB-Qdrant-ff6b6b?style=flat-square&logo=qdrant" alt="Qdrant"></a>
  <a href="https://min.io/"><img src="https://img.shields.io/badge/Storage-MinIO-f79533?style=flat-square&logo=minio" alt="MinIO"></a>
  <a href="https://docs.docker.com/compose/"><img src="https://img.shields.io/badge/Orchestration-Docker-2496ed?style=flat-square&logo=docker" alt="Docker"></a>
</p>

# Snappy - Vision-Grounded Document Retrieval

  Snappy pairs a FastAPI backend, ColPali embedding service, DeepSeek OCR, DuckDB analytics, and a Next.js frontend to deliver hybrid vision+text retrieval over PDFs. Each page is rasterized, embedded as multivectors, and stored alongside images and optional OCR text so you can search by visual layout, extracted text, or both.



## Showcase 🎬

https://github.com/user-attachments/assets/99438b0d-c62e-4e47-bdc8-623ee1d2236c


## Quick start
Prereqs: Docker with Compose, Make (or use the equivalent `docker compose` commands below).

1) Copy envs and set the essentials  
`cp .env.example .env`  
Set `OPENAI_API_KEY` (required for chat). Other defaults are ready for local use.

2) Choose a profile  
- Minimal (ColPali only; works on CPU or GPU): `make up-minimal`  
- ML (adds DeepSeek OCR; needs NVIDIA GPU): `make up-ml`  
- Full (adds DuckDB analytics and deduplication): `make up-full`  
If you prefer Compose directly: `docker compose --profile minimal|ml|full up -d`.

3) Open the UI  
- Frontend: http://localhost:3000  
- Backend: http://localhost:8000/docs (OpenAPI)  
- DuckDB UI (full profile): http://localhost:42130

## Architecture
![unnamed 4](https://github.com/user-attachments/assets/40a4f985-0445-42d9-8984-4a6ddca886a6)


## Modes and options
| Feature | When to enable | How |
|---------|----------------|-----|
| DeepSeek OCR | Need extracted text, markdown, or bounding boxes alongside visual retrieval; have an NVIDIA GPU. | Set `DEEPSEEK_OCR_ENABLED=true` and run `make up-ml` or profile `ml`. |
| DuckDB analytics | Want deduplication, inline OCR results from the backend, or SQL over OCR regions. | Set `DUCKDB_ENABLED=true` and run `make up-full` or profile `full`. |
| Mean pooling re-ranking | Improve search accuracy with two-stage retrieval (prefetch + re-rank). More accurate but requires more compute. | Set `QDRANT_MEAN_POOLING_ENABLED=true` in `.env`. Requires ColPali model with `/patches` support (enabled in `colmodernvbert`). |
| Binary quantization | Large collections and tight RAM/GPU budget (32x memory reduction). | Enabled by default. Toggle in `.env` if needed. |

## Troubleshooting highlights
- Progress stuck on upload/indexing: ensure Poppler is installed for PDF rasterization and check backend logs.  
- Missing images: confirm MinIO credentials/URLs and allowed domains in `frontend/next.config.ts`.  
- OCR not running: `DEEPSEEK_OCR_ENABLED=true`, GPU profile running, and `/ocr/health` reachable.  
- Config not sticking: `/config/update` is runtime-only; edit `.env` for persistence.

## Where to go next
- `STREAMING_PIPELINE.md` - how the streaming indexer works.  
- `backend/docs/architecture.md` - deeper component and flow description.  
- `backend/docs/configuration.md` - full config reference.  
- `backend/docs/analysis.md` - when to use vision vs text.  
- `frontend/README.md`, `backend/README.md` - service-specific guides.

## License
MIT License (see `LICENSE`).
