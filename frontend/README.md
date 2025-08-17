# Vision RAG Frontend (Next.js 15)

Next.js App Router UI for upload/indexing, search, and chat.

- Codegen: `openapi-typescript-codegen` + `openapi-zod-client`
- Generated SDK wired via `frontend/lib/api/client.ts`

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

## Docker/Compose
- The repo root `docker-compose.yml` includes a `frontend` service (Next.js on 3000).
- Start all services from the repo root:
```bash
docker compose up -d --build
```
