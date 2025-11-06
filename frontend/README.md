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
- Allows editing settings locally with real-time validation and draft detection.
- Changes are only applied to the backend when clicking "Save Changes".
- Provides "Reset section" and "Reset all" buttons to restore defaults without auto-applying.
- Drafts persist in `localStorage` (`colpali-runtime-config`) so you can compose changes before applying them.
- Critical settings trigger backend cache invalidation automatically when saved.
- All updates (including resets) are applied via individual `POST /config/update` calls for safety.

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

---

## State Management Architecture

The application uses a refactored state management system organized by separation of concerns.

### Structure

```
stores/
├── app-store.tsx          # Main store provider, context, and hook re-exports
├── types.ts               # State, action, and initial state definitions
├── reducers/              # Domain-specific reducers
│   ├── index.ts           # Reducer composition
│   ├── search-reducer.ts  # Search state logic
│   ├── chat-reducer.ts    # Chat state logic
│   ├── upload-reducer.ts  # Upload state logic
│   ├── system-reducer.ts  # System status logic
│   └── global-reducer.ts  # Global actions (hydration, page tracking)
└── utils/                 # Utility helpers
    └── storage.ts         # LocalStorage serialization/deserialization
```

Domain hooks live under `lib/hooks` (`use-search-store.ts`, `use-chat-store.ts`, `use-upload-store.ts`, `use-system-status.ts`, `use-upload-sse.ts`) and are re-exported from `app-store.tsx` for convenience.

### Usage

**Using the Store Provider:**

Wrap your app with the provider:

```tsx
import { AppStoreProvider } from '@/stores/app-store';

<AppStoreProvider>
  <YourApp />
</AppStoreProvider>
```

**Using Domain Hooks:**

Import and use the specific hook you need:

```tsx
import { useSearchStore } from '@/stores/app-store';

function SearchComponent() {
  const { query, results, setQuery, setResults } = useSearchStore();
  // ... component logic
}
```

Available hooks:
- `useSearchStore()` - Search state and actions
- `useChatStore()` - Chat state and actions
- `useUploadStore()` - Upload state and actions
- `useSystemStatus()` - System status and health checks

**Accessing Raw State/Dispatch:**

For advanced use cases:

```tsx
import { useAppStore } from '@/stores/app-store';

function Component() {
  const { state, dispatch } = useAppStore();
  // Direct access to full state and dispatch
}
```

### Benefits

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Maintainability** - Easy to locate and modify specific functionality
3. **Testability** - Individual reducers and utilities can be tested in isolation
4. **Scalability** - New domains can be added without modifying existing code
5. **Type Safety** - Centralized types ensure consistency across the application
6. **Code Reusability** - Utilities and hooks can be shared across components

### Adding New Features

**Adding a New Action:**

1. Add the action type to `types.ts`
2. Create/update the appropriate reducer in `reducers/`
3. Add action creators to the relevant hook in `hooks/`

**Adding a New Domain:**

1. Define types in `types.ts`
2. Create a new reducer in `reducers/[domain]-reducer.ts`
3. Add the reducer to the composition in `reducers/index.ts`
4. Create a new hook under `lib/hooks/use-[domain]-store.ts`
5. Export the hook from `lib/hooks/index.ts` (if applicable) and re-export it from `app-store.tsx`

````
