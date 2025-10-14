
# Snappy frontend (Next.js 15)

Snappy's UI is built with the Next.js App Router, Tailwind v4, shadcn, and Framer Motion. Pages stay intentionally minimal so you can tailor the experience without ripping out heavy custom styling.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing page with quick calls to action |
| `/about` | Explains the stack and how to extend Snappy |
| `/upload` | Drag-and-drop ingestion with SSE progress and cancel support |
| `/search` | Visual search UI with example prompts and inline previews |
| `/chat` | Streaming assistant, tweakable retrieval settings, visual citations |
| `/maintenance` | Two tabs: configuration editor and maintenance actions |

Codegen is handled by `openapi-typescript-codegen` and `openapi-zod-client`; generated files live under `frontend/lib/api/generated`.

## Setup

```powershell
cd frontend
yarn install --frozen-lockfile
yarn dev
# http://localhost:3000
```

Create `frontend/.env.local` if you need to override defaults:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini   # optional
OPENAI_TEMPERATURE=1      # optional
OPENAI_MAX_TOKENS=1500    # optional
```

The chat route (`app/api/chat/route.ts`) reads `OPENAI_*` on the server and streams OpenAI Responses API events back to the browser.

## Scripts

```powershell
yarn dev            # start Next.js with Turbopack
yarn build          # production build
yarn start          # run built app
yarn gen:sdk        # regenerate REST client from docs/openapi.json
yarn gen:zod        # regenerate Zod typings
```

## Styling

- Tailwind v4 with CSS variables defined in `app/globals.css`.
- shadcn components stored under `components/ui`.
- Light Framer Motion usage for fades and entrance animations; no custom motion presets.

## Project structure

```
frontend/
├─ app/                # Routes, layouts, API handlers
├─ components/         # Reusable UI, upload widgets, chat helpers
├─ lib/                # API client, hooks, configuration store
├─ stores/             # Global state (Zustand)
└─ docs/openapi.json   # Source for generated SDKs
```

## Maintenance tab

The maintenance view talks to backend `/config/*` and `/status` endpoints:

- Edit runtime configuration by category.
- Initialise or delete the Qdrant collection and MinIO bucket.
- Run critical maintenance actions (clear Qdrant/MinIO/all).

All requests run through the generated SDK and show toast feedback in the UI.
