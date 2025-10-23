# Snappy Frontend – Next.js Interface 🎨

This Next.js 16 application (with React 19.2) provides upload, search, chat, configuration, and maintenance workflows for Snappy. Types and SDKs are generated from the backend OpenAPI schema and wired through `frontend/lib/api/client.ts`.

---

## Pages

- **`/`** – Landing page with quick links and an overview.
- **`/about`** – Background on Snappy and the ColPali approach.
- **`/upload`** – PDF uploads with live SSE progress and cancel support.
- **`/search`** – Vision-based search with metadata for each page.
- **`/chat`** – Conversational experience backed by OpenAI Responses API and visual citations.
- **`/configuration`** – Runtime configuration UI with draft detection and granular updates.
- **`/maintenance`** – Status dashboards plus initialise/delete/reset helpers.

---

## Design Language

- Design tokens live in `app/globals.css` (`text-body-*`, `size-icon-*`, etc.) and keep typography and spacing consistent.
- Shared components rely on these utilities; use them when extending the UI to maintain visual balance.

---

## Requirements

- **Node.js 22** (matches the Docker image)
- **Yarn Classic (v1)** – enabled via `corepack`; npm works if you prefer.

---

## Setup

```bash
yarn install --frozen-lockfile
```

Environment variables go in `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini        # optional
OPENAI_TEMPERATURE=1           # optional
OPENAI_MAX_TOKENS=1500         # optional
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000` if unset.

---

## Development

```bash
yarn dev
```

Visit http://localhost:3000 to start building.

For production:

```bash
yarn build
yarn start
```

---

## Type-Safe API Access

- The SDK (`lib/api/generated`) and Zod schemas (`lib/api/zod.ts`) are generated from `docs/openapi.json`.
- Codegen runs automatically on `predev` and `prebuild`. Regenerate manually with:

```bash
yarn gen:sdk && yarn gen:zod
```

---

## Chat API (Edge Runtime)

- Endpoint: `POST /api/chat`
- Request body:

```json
{
  "message": "Explain this",
  "k": 5,
  "toolCallingEnabled": true
}
```

- Response: `text/event-stream` with:
  - `response.output_text.delta` events for text streaming
  - `kb.images` events describing visual citations (URLs, labels, relevance)
  - OpenAI passthrough events (safe to ignore if not needed)

Behaviour:
- With tool calling disabled, the route always performs a document search and emits images when results exist.
- With tool calling enabled, the AI decides when to call `document_search`; images are emitted only if the tool runs.

---

## Citations Walkthrough

1. Open `/chat`.
2. Toggle tool calling in settings.
3. With tools disabled, ask something document-related—citations appear on every response that finds matches.
4. With tools enabled, the AI chooses whether to search; general questions may stream without images.
5. K value (results count) and tool calling preferences persist via `localStorage`.

---

## Configuration UI

- Fetches schema via `GET /config/schema` and values via `GET /config/values`.
- Updates a single setting with `POST /config/update` and restores defaults with `POST /config/reset`.
- Drafts live in `localStorage` (`colpali-runtime-config`) so you can compose changes before applying them.
- Critical settings trigger backend cache invalidation automatically.

For the full backend configuration reference see `../backend/docs/configuration.md`.

---

## Docker Compose

The root `docker-compose.yml` runs the frontend alongside other services. Example environment block:

```yaml
services:
  frontend:
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
      - OPENAI_API_KEY=sk-your-key
      - OPENAI_MODEL=gpt-5-nano
      - OPENAI_TEMPERATURE=1
      - OPENAI_MAX_TOKENS=1500
```

`NEXT_PUBLIC_API_BASE_URL` is evaluated at build time, so rebuild the image when changing it. OpenAI variables are read at runtime.
