# Snappy Frontend - The Face of Brilliance! 🎨

Welcome to Snappy's gorgeous Next.js 15 interface! This is where the magic meets the eye; beautiful pages for uploading, searching, and chatting with your documents.

- Codegen: `openapi-typescript-codegen` + `openapi-zod-client`
- Generated SDK wired via `frontend/lib/api/client.ts`

## Your Tour of Snappy's Pages 🗺️

We keep things clean, simple, and unauthenticated (for now). Here's what you'll find:

- **`/`** - 🏠 **Home Sweet Home**: Your Snappy-branded landing pad with quick links and an overview of what's possible.

- **`/about`** - 📖 **The Story**: Learn what Snappy does, how ColPali works its magic, and why vision-first beats old-school text-only RAG.

- **`/upload`** - 📤 **Drop Your Docs**: Upload PDFs and watch them get indexed in real-time. Background jobs via `POST /index` with live progress through SSE streams. Changed your mind? Hit cancel!

- **`/search`** - 🔍 **Find What You Need**: Visual search across all indexed pages. Get your top-k results with full metadata.

- **`/chat`** - 💬 **Talk to Your Docs**: AI-powered conversations grounded in retrieved page images. Visual citations included, with Snappy's friendly callouts!

- **`/configuration`** - ⚙️ **Control Center**: Manage all backend settings through a slick web UI. Section tabs, draft detection, and real-time updates; no backend restarts needed!

- **`/maintenance`** - 🛠️ **System Command**: Your system management hub featuring:
  - 📊 Real-time status dashboard (system health, vector counts, file stats)
  - 🎬 **Initialize System**: First-time setup for Qdrant + MinIO
  - 🗑️ **Delete System**: Nuclear option for fresh starts
  - 🔄 **Data Reset**: Clear everything while keeping infrastructure intact
  - ✅ Confirmation dialogs and live status updates everywhere

## Snappy's Design Language 🎨

- **Design Tokens Rule**: All typography (`text-body`, `text-body-xs`, `text-body-lg`) and icon sizing (`size-icon-*`) live in `app/globals.css`. One source of truth, zero guesswork!

- **Consistency by Default**: Shared components use these utilities exclusively. Responsive variants (`sm:text-body-sm`, `md:size-icon-md`) keep everything looking sharp on any screen.

- **Build with Style**: When creating new components, stick to our token utilities instead of raw Tailwind classes. Your future self will thank you! 🙏

## What You'll Need 📦
- **Node.js 22** - Matches our Dockerfile for consistency
- **Yarn Classic (v1)** - Auto-enabled by `corepack` in Docker. Locally? Use Yarn or npm, we're flexible!

## Installation Time! 🚀
```bash
# Install all the frontend goodies
yarn install --frozen-lockfile
```

## Environment Setup 🌟

**Backend Connection**:
```bash
# Point Snappy to your backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
*Default is `http://localhost:8000` if not set; we got you covered!*

**OpenAI Configuration** (for that sweet chat magic):
```bash
# Your OpenAI credentials
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini        # Optional: pick your model
OPENAI_TEMPERATURE=1           # Optional: creativity dial
OPENAI_MAX_TOKENS=1500         # Optional: response length
```
*The chat route (`frontend/app/api/chat/route.ts`) uses these to stream beautiful responses via SSE!*

## Start Developing 💻
```bash
yarn dev
```
🎉 **Boom!** Head to http://localhost:3000 and start building!

## Production Build 🏗️
```bash
# Build for production
yarn build

# Run the optimized build
yarn start
```

## Type-Safe Magic 🪄

**Auto-Generated Types**: Our SDK and Zod schemas come straight from `frontend/docs/openapi.json`. Always in sync, always type-safe!

**Codegen**: Happens automatically on `predev` and `prebuild`. Want to regenerate manually?
```bash
yarn gen:sdk && yarn gen:zod
```
*Perfect for when you've updated the backend API schema!*

## Chat API - Streaming Excellence 🌊

**Endpoint**: `POST /api/chat`  
**Runtime**: Edge Runtime (blazing fast, minimal latency!)

**Send This**:
```json
{
  "message": "Explain this",
  "k": 5,
  "toolCallingEnabled": true
}
```

**Get This** (`text/event-stream`):
- 📝 `response.output_text.delta` - Text streaming in chunk by chunk
- 🖼️ `kb.images` - Visual citations with URLs, labels, and relevance scores
- 🔄 OpenAI passthroughs - Other events (safely ignored by the UI)

**How It Works**:
- 🔧 **Tools OFF**: Backend always searches docs and emits images when found
- 🤖 **Tools ON**: Backend only emits images if the AI decides to call the `document_search` tool
- ✨ **UI Magic**: Glowing "Visual citations included" chip appears, click to scroll to the gallery!

## Visual Citations Deep Dive 🎯

**When Do Images Appear?**

- **🔴 Tools Disabled**
  - Every query triggers document search
  - Images included when results exist
  - Predictable and consistent!

- **🟢 Tools Enabled**
  - AI decides when to search documents
  - Images only appear when the tool is invoked
  - Smarter, but less predictable

**Testing the Magic** 🧪

1. Head to `/chat`
2. Toggle Tool Calling in settings
3. **Tools OFF**: Ask "What are the key risks?" → Citations appear!
4. **Tools ON**: Try "Find diagrams about AI architecture" → Tool invoked, images shown
5. **Tools ON**: Ask "What's 2+2?" → No tool needed, no images (as expected!)

**Control the Behavior** 🎮
- Toggle tools in the UI or set `localStorage['tool-calling-enabled'] = 'false'`
- Adjust K value (result count) via the slider; persists to `localStorage['k']`

## Configuration Management - Total Control ⚙️

The `/configuration` page is your mission control for all backend settings:

### Why You'll Love It 💙
- ✏️ **Live Editing**: Change any setting through a beautiful UI
- 📁 **Smart Organization**: Settings grouped by Application, Processing, ColPali, Qdrant, MinIO, and MUVERA
- 🎚️ **Smart Controls**: Sliders for numbers, toggles for booleans, dropdowns for choices
- ✅ **Instant Validation**: Min/max ranges, tooltips, and helpful error messages
- 👁️ **Conditional UI**: Dependent settings appear/disappear based on context
- 💾 **Draft System**: Local changes cached in `localStorage`; you decide when to apply them!
- 🔄 **Reset Superpowers**: Reset individual sections or go nuclear and reset everything

### Under the Hood 🔧
- `GET /config/schema` - Grab the config blueprint with all metadata
- `GET /config/values` - See what's currently set
- `POST /config/update` - Change individual settings on the fly
- `POST /config/reset` - Back to square one (defaults restored)

### Important Stuff ⚠️
- ⚡ Changes take effect **immediately** in the runtime
- 💨 Changes are **temporary**; container restarts wipe them
- 💾 For permanent changes, update your `.env` file
- 🔄 Critical settings (like API URLs) trigger service restarts automatically
- 📦 Draft system uses `localStorage` (`colpali-runtime-config`); version-controlled and smart!
- 📖 Deep dive: Check [backend/docs/configuration.md](../backend/docs/configuration.md) for all the details

## Docker Compose - One Command Deploy 🐳

The root `docker-compose.yml` includes our `frontend` service (Next.js on port 3000).

**Launch Everything**:
```bash
docker compose up -d --build
```

**Environment Variables** (set these on the frontend container):
```yaml
services:
  frontend:
    environment:
      - OPENAI_API_KEY=sk-your-key
      - OPENAI_MODEL=gpt-5-nano           # optional
      - OPENAI_TEMPERATURE=1              # optional
      - OPENAI_MAX_TOKENS=1500            # optional
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Pro Tips** 💡:
- `NEXT_PUBLIC_API_BASE_URL` bakes in at build time (defaults to `http://localhost:8000`)
- `OPENAI_*` variables are read at server runtime; set them on the container and you're golden!
