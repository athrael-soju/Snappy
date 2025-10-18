# Vision RAG Frontend (Next.js 15)

Next.js App Router UI for upload/indexing, search, and chat.

- Codegen: `openapi-typescript-codegen` + `openapi-zod-client`
- Generated SDK wired via `frontend/lib/api/client.ts`

## Pages & Routes

The app is intentionally simple and unauthenticated. Current pages:

- `/` - Home: Snappy-branded landing with quick links and overview.
- `/about` - About: what this project does, what ColPali is, and comparison to traditional text-only RAG.
- `/upload` - Upload PDFs for indexing. Starts a background job via FastAPI `POST /index` and subscribes to `GET /progress/stream/{job_id}` (SSE) for real-time progress. Includes upload cancellation support.
- `/search` - Visual search over indexed pages; returns top-k pages and metadata.
- `/chat` - AI chat grounded on retrieved page images with visual citations and Snappy callouts.
- `/configuration` - Web-based UI for managing backend environment variables at runtime with section tabs and an explicit draft-restore flow (see Configuration Management below).
- `/maintenance` - System maintenance interface with:
  - Real-time status display showing system readiness, collection stats (vectors, unique files), and bucket stats (object count)
  - **Initialize System**: Creates the Qdrant collection and prepares the MinIO bucket. Required before first use.
  - **Delete System**: Removes both the collection and the MinIO bucket for configuration changes or a fresh start.
  - **Data Reset**: Clears all data (documents, embeddings, images) while preserving the collection and bucket infrastructure.
  - All operations include confirmation dialogs and status updates across all pages via event system.

## Design System

- **Tokens live in `app/globals.css`**. Typography utilities (`text-body`, `text-body-xs`, `text-body-lg`) and icon utilities (`size-icon-*`) define our spacing scale.
- Shared components outside `components/ui` rely on these utilities exclusively, keeping the stylesheet the single source of truth. Responsive variants (e.g. `sm:text-body-sm`, `md:size-icon-md`) are provided in the same file.
- When building new components, prefer the token utilities over raw Tailwind primitives (`text-sm`, `h-4`, etc.) so spacing stays consistent.

## Requirements
- Node.js 22 (matches Dockerfile)
- Yarn Classic (v1) - auto-enabled by `corepack` in Docker. Locally you can use Yarn or npm.

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
`frontend/lib/api/client.ts` falls back to `http://localhost:8000` if the env var is not set. The Upload page uses `fetch` for `POST /index` and `EventSource` for `GET /progress/stream/{job_id}`.

OpenAI for chat (SSE) - set on the frontend (server runtime):
```bash
# frontend/.env.local
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini   # optional override
# optional
OPENAI_TEMPERATURE=1
OPENAI_MAX_TOKENS=1500
```
The chat endpoint `frontend/app/api/chat/route.ts` uses these to call OpenAI Responses API and stream tokens via Server-Sent Events (SSE) to the browser.

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
- The SDK and Zod types are generated from `frontend/docs/openapi.json` and are used across pages. The Upload page currently calls `POST /index` via `fetch` and uses `EventSource` for `GET /progress/stream/{job_id}`.
- Codegen runs automatically via `predev` and `prebuild` scripts. To (re)generate manually:
```bash
yarn gen:sdk && yarn gen:zod
```

## Chat API (SSE)
- Route: `POST /api/chat`
- Runtime: **Edge Runtime** for optimized streaming performance and reduced latency
- Request body:
  ```json
  {
    "message": "Explain this",
    "k": 5,
    "toolCallingEnabled": true
  }
  ```
- Response: `text/event-stream` (SSE). Events include:
  - `response.output_text.delta` - incremental assistant text tokens `{ event, data: { delta: string } }`
  - `kb.images` - visual citations used by the model `{ event, data: { items: [{ image_url, label, score }] } }`
  - Other OpenAI event passthroughs are sent with `{ event: <type>, data: <raw> }` and are ignored by the UI

Notes:

- When tool calling is disabled, the backend performs document search unconditionally and emits `kb.images` if results exist. When tool calling is enabled, `kb.images` is emitted only if the model actually calls the `document_search` tool.
- The UI listens for `kb.images` and shows a glowing "Visual citations included" chip; clicking scrolls to the gallery.

## Tool calling & visual citations

When are images emitted?

- Tools OFF (disabled)
  - Backend always runs document search before answering
  - Emits `kb.images` if results exist

- Tools ON (enabled)
  - Backend exposes the `document_search` tool to the model
  - Emits `kb.images` only if the model called the tool and images were attached

Testing

1) Visit `/chat`
2) Toggle Tool Calling in the settings chip
3) OFF: ask a grounded question (e.g. "What are the key risks?") and observe the citations chip + gallery
4) ON: ask a retrieval question to induce a tool call (e.g. "Find diagrams about AI architecture"). Also try a generic question where the tool is not needed - no images should appear

Deterministic behavior

- Disable tools via the UI or set `localStorage['tool-calling-enabled'] = 'false'`
- Adjust top-K via the K control (persists to `localStorage['k']`)

## Configuration Management

The `/configuration` page provides a web-based interface for managing backend environment variables:

### Features
- **Live editing**: Modify all backend configuration values through an intuitive UI
- **Categorized settings**: Organized by Application, Processing, ColPali API, Qdrant, MinIO, and MUVERA
- **Smart controls**: Sliders for numeric values, toggles for booleans, dropdowns for enums
- **Real-time validation**: Input constraints, min/max ranges, and tooltips
- **Conditional visibility**: Dependent settings show/hide based on parent values
- **Draft awareness**: Local edits are cached in `localStorage`, but you choose whether to restore them before anything is written back to the API
- **Reset options**: Reset individual sections or all settings to defaults

### API Endpoints Used
- `GET /config/schema` - retrieves configuration schema with metadata
- `GET /config/values` - fetches current runtime values
- `POST /config/update` - updates individual settings
- `POST /config/reset` - resets all settings to defaults

### Important Notes
- Configuration changes update the backend **runtime environment** immediately
- Changes are **not persisted** to the `.env` file and will be lost on container restart
- For permanent changes, manually update your `.env` file
- Critical settings (e.g., API URLs) trigger service invalidation and re-initialization
- Browser persistence uses a versioned `localStorage` payload (`colpali-runtime-config`); when cached values differ from the server the page surfaces a draft banner so you can restore or discard them before saving.
- See [backend/docs/configuration.md](../backend/docs/configuration.md) for detailed setting documentation

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
        - OPENAI_MODEL=gpt-5-nano # optional
        - OPENAI_TEMPERATURE=1     # optional
        - OPENAI_MAX_TOKENS=1500   # optional
        - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
  ```
  Notes:
  - `NEXT_PUBLIC_API_BASE_URL` is embedded at build time; the app defaults to `http://localhost:8000` if unset.
  - The chat API route reads `OPENAI_*` at server runtime, so setting them on the running container is sufficient.
