# Morty™ Frontend – The Face of Vision Retrieval

Morty’s frontend is a Next.js 15 application that retains the Snappy UX while adopting the updated brand identity. It delivers uploading, searching, chatting, configuration, and maintenance workflows with streamed responses and citation overlays. Code generation, storage, and API bindings remain unchanged.

- Code generation: `openapi-typescript-codegen` + `openapi-zod-client`  
- Generated SDK bootstrap: `frontend/lib/api/client.ts`

## Page Tour

- `/` – Landing page with quick links and onboarding.  
- `/about` – Explains Morty’s vision-first approach and the Vultr collaboration.  
- `/upload` – Upload PDFs; progress events stream over `POST /index` with SSE updates.  
- `/search` – Run visual searches and inspect metadata-rich results.  
- `/chat` – Ask questions; streamed answers include thumbnail citations.  
- `/configuration` – Manage backend settings with typed inputs and draft detection.  
- `/maintenance` – Initialize, reset, or tear down Qdrant and MinIO resources and review system health.

## Design System

- Typography and icon sizing tokens live in `app/globals.css` (`text-body-*`, `size-icon-*`).  
- Shared components rely on these tokens to guarantee consistency in dark and light themes.  
- New components should use token utilities instead of bespoke Tailwind classes to preserve Morty’s visual rhythm.  
- Follow Vultr’s Morty™ guidelines: energetic copy, approachable tone, technology-savvy vocabulary, and AA contrast.

## Prerequisites

- Node.js 22 (matches the Dockerfile)  
- Yarn Classic (v1) – automatically enabled by `corepack`

## Install Dependencies

```bash
yarn install --frozen-lockfile
```

## Environment Variables

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini          # optional
OPENAI_TEMPERATURE=1             # optional
OPENAI_MAX_TOKENS=1500           # optional
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`. Morty continues to stream chat responses via `frontend/app/api/chat/route.ts`, so OpenAI credentials must be present before you start the server.

## Development

```bash
yarn dev
# Visit http://localhost:3000
```

## Production Build

```bash
yarn build
yarn start
```

## Type Generation

API clients and Zod validators stay in sync with the backend OpenAPI spec stored in `frontend/docs/openapi.json`.

```bash
yarn gen:sdk
yarn gen:zod
```

These commands run automatically before `yarn dev` and `yarn build`.

## Chat API Highlights

- Endpoint: `POST /api/chat` (Edge runtime)  
- Request body:

```json
{
  "message": "Explain this",
  "k": 5,
  "toolCallingEnabled": true
}
```

- SSE events:
  - `response.output_text.delta` – streamed text.  
  - `kb.images` – citation images with labels and scores.

Tool-calling controls remain in the UI. Disabling tool calling forces Morty to run document search for every prompt, mirroring the original Snappy behavior.

## Configuration Console

- Fetches metadata from `GET /config/schema` and values from `GET /config/values`.  
- Submits updates through `POST /config/update` with field-level validation feedback.  
- Draft state lives in `localStorage` until changes are applied, allowing safe experimentation.  
- Resets can target individual sections or the entire configuration.  
- Critical setting changes trigger cache invalidation without restarting the backend.

## Docker Compose

The root `docker-compose.yml` launches the frontend alongside the backend and supporting services.

```bash
docker compose up -d --build
```

Example environment configuration:

```yaml
services:
  frontend:
    environment:
      - OPENAI_API_KEY=sk-your-key
      - OPENAI_MODEL=gpt-5-nano
      - OPENAI_TEMPERATURE=0.8
      - OPENAI_MAX_TOKENS=1200
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
```

Remember: `NEXT_PUBLIC_API_BASE_URL` is baked during build; rebuild when changing it.

## Migration Notes

- All routes, components, and API calls keep their original names to preserve compatibility.  
- Copy, alt text, and metadata reference Morty instead of Snappy.  
- Review `MIGRATION.md` for branding updates and FAQs, and consult `TRADEMARKS.md` for Morty-specific usage rules.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
