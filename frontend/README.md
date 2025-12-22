# Snappy Frontend - Next.js Interface

Next.js 16 (React 19) app for upload, search, chat, configuration, and maintenance. Uses the generated OpenAPI SDK (`@/lib/api/generated`).

## Setup
Prereqs: Node 22, Yarn Classic (via corepack).

```bash
yarn install --frozen-lockfile
cp .env.local.example .env.local  # if present; otherwise create .env.local
```

Key envs (`frontend/.env.local`):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-nano        # optional
OPENAI_TEMPERATURE=1           # optional
OPENAI_MAX_TOKENS=1500         # optional
```

## Develop & build
```bash
yarn dev        # http://localhost:3000
yarn build
yarn start
```

## API usage
- Always call the backend via the generated SDK (`@/lib/api/generated`), not manual `fetch`.
- Client wrapper lives in `lib/api/client.ts`.

## Pages
- Upload, Search, Chat, Configuration, Maintenance (status/init/delete/reset).

## Logging and state
- Use `lib/utils/logger.ts` for structured logging.
- Global state lives in `stores/app-store.tsx` with hooks under `lib/hooks` (`use-search-store`, `use-chat-store`, `use-upload-store`, `use-system-status`).

## Docker Compose
Root `docker-compose.yml` example:
```yaml
services:
  frontend:
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
      - OPENAI_API_KEY=sk-your-key
```
`NEXT_PUBLIC_API_BASE_URL` is evaluated at build time; rebuild the image after changing it.
