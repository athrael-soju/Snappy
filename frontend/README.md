# Vision RAG Frontend (Next.js 15)

Next.js App Router UI for upload/indexing, search, and chat.

- Codegen: `openapi-typescript-codegen` + `openapi-zod-client`
- Generated SDK wired via `frontend/lib/api/client.ts`

## Pages & Routes

The app is intentionally simple and unauthenticated. Current pages:

- `/` — Home: landing with quick links and overview.
- `/about` — About: what this project does, what ColPali is, and comparison to traditional text-only RAG.
- `/upload` — Upload PDFs for indexing (sent to FastAPI `/index`).
- `/search` — Visual search over indexed pages; returns top-k pages and metadata.
- `/chat` — AI chat grounded on retrieved page images.
- `/maintenance` — Destructive admin actions (clear Qdrant, clear MinIO, clear all) with confirmations.

Screenshots live in `image/README/` and are referenced from the repo root `README.md`.

## Requirements
- Node.js 22 (matches Dockerfile)
- Yarn Classic (v1) — auto-enabled by `corepack` in Docker. Locally you can use Yarn or npm.

## Install
```bash
# From frontend/
yarn install --frozen-lockfile
# or: npm ci
```

## Environment
Set the backend base URL for the SDK and fetches:
```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
`frontend/lib/api/client.ts` falls back to `http://localhost:8000` if the env var is not set.

OpenAI for chat (SSE) — set on the frontend (server runtime):
```bash
# frontend/.env.local
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini   # optional override
# optional
OPENAI_TEMPERATURE=1
OPENAI_MAX_TOKENS=1500
```
The chat endpoint `frontend/app/api/chat/route.ts` uses these to call OpenAI Responses API and stream tokens via Server‑Sent Events (SSE) to the browser.

## Develop
```bash
yarn dev
# or: npm run dev
```
Open http://localhost:3000.

## Build & Run
```bash
yarn build
yarn start
```

## API Schema & Codegen
- The SDK and Zod types are generated from `frontend/docs/openapi.json`.
- Generation runs automatically via `predev` and `prebuild` scripts.
- To (re)generate manually:
```bash
yarn gen:sdk && yarn gen:zod
```

## Chat API (SSE)
- Route: `POST /api/chat`
- Body:
  ```json
  {
    "message": "Explain this",
    "images": [{ "image_url": "http://localhost:9000/documents/images/...png" }],
    "systemPrompt": "You are a helpful assistant"
  }
  ```
- Response: `text/event-stream` of OpenAI Responses events. The UI consumes this stream to render the assistant message progressively.

## Docker/Compose
- The repo root `docker-compose.yml` includes a `frontend` service (Next.js on 3000).
- Start all services from the repo root:
  ```bash
  docker compose up -d --build
  ```
- OPENAI_* for chat must be provided to the frontend container at runtime (the backend does not use them):
  ```yaml
  services:
    frontend:
      environment:
        - OPENAI_API_KEY=sk-your-key
        - OPENAI_MODEL=gpt-4o-mini # optional
        - OPENAI_TEMPERATURE=1     # optional
        - OPENAI_MAX_TOKENS=1500   # optional
        - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
  ```
  Notes:
  - `NEXT_PUBLIC_API_BASE_URL` is embedded at build time; the app defaults to `http://localhost:8000` if unset.
  - The chat API route reads `OPENAI_*` at server runtime, so setting them on the running container is sufficient.
