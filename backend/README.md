# Snappy Backend - Where the Magic Happens! ✨

Welcome to Snappy's brain! This FastAPI service is the powerhouse behind PDF ingestion, lightning-fast page-level retrieval, and all those sweet system maintenance features. 

Everything's neatly organized in modular routers under `backend/api/routers/` (`meta`, `retrieval`, `indexing`, `maintenance`, `config`), all fired up through `backend/api/app.py:create_app()`. Clean architecture? You bet! 🏛️

## What You'll Need 📦

- **Python 3.10+** - The newer, the better!
- **Poppler** - Must be on your `PATH` (Snappy uses `pdftoppm` for PDF magic)
- **Docker + Docker Compose** - Optional but highly recommended for a smooth ride
- **`fastembed[postprocess]`** - Optional, only if you want MUVERA superpowers

## Getting Started Locally 🚀

```bash
# Create a cozy virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Update the essentials
pip install -U pip setuptools wheel

# Install Snappy's backend dependencies
pip install -r backend/requirements.txt
```

## Environment Setup 🌟

```bash
# Copy the example env file
copy .env.example .env
```

**Essential Variables** (peek at `.env.example` and `backend/config.py` for details):

- **ColPali Config**: `COLPALI_MODE`, `COLPALI_CPU_URL`, `COLPALI_GPU_URL`, `COLPALI_API_TIMEOUT`
- **Qdrant Setup**: `QDRANT_EMBEDDED`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, plus quantization options
- **MinIO Storage**: `MINIO_URL`, `MINIO_PUBLIC_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

**Default Endpoints** (works out of the box!):
- 🕸️ Qdrant: `http://localhost:6333`
- 🗄️ MinIO: `http://localhost:9000`
- 🧠 ColPali CPU: `http://localhost:7001`
- 🚀 ColPali GPU: `http://localhost:7002`

📚 **Deep Dive**: Check out `backend/docs/configuration.md` for the complete configuration encyclopedia!

## Fire Up the Backend 🔥

```bash
# Option 1: The uvicorn way (with hot reload!)
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

# Option 2: The direct approach
python backend/main.py
```

🎉 **Ready to explore?** Head to http://localhost:8000/docs for interactive API documentation!

## Docker Compose - The Easy Button 🐳

Our root `docker-compose.yml` orchestrates the whole gang: `qdrant`, `minio`, `backend`, and `frontend`. Everything just works!

**Container Configuration**:
- `COLPALI_CPU_URL=http://host.docker.internal:7001`
- `COLPALI_GPU_URL=http://host.docker.internal:7002`
- `QDRANT_URL=http://qdrant:6333`
- `MINIO_URL=http://minio:9000`
- `MINIO_PUBLIC_URL=http://localhost:9000`

**Launch Everything**:
```bash
docker compose up -d --build
```

⚠️ **Important**: MinIO credentials are mandatory. Snappy needs proper object storage; no shortcuts here!

## API Endpoints - Your Command Center 🎮

### 💓 Meta (Health Checks)

- `GET /health` – See how ColPali, MinIO, and Qdrant are feeling

### 🔍 Retrieval (The Search Magic)

- `GET /search?q=...&k=5` – Visual search across all indexed documents  
  (Leave out `k` for a sensible 10 results)

### 📚 Indexing (Document Processing)

- `POST /index` – Upload PDFs (multipart `files[]`) and start the magic
- `GET /progress/stream/{job_id}` – Real-time progress via Server-Sent Events
- `POST /index/cancel/{job_id}` – Changed your mind? Cancel away!

### 🛠️ Maintenance (System Management)

- `GET /status` – Quick stats on your collection and bucket
- `POST /initialize` – Set up collection + bucket (first time? Start here!)
- `DELETE /delete` – Nuclear option: removes collection and bucket
- `POST /clear/qdrant` – Wipe Qdrant data only
- `POST /clear/minio` – Clear MinIO objects only
- `POST /clear/all` – Fresh start: clear everything!

*Note: MinIO deletes give you detailed reports, even when things go sideways.*

### ⚙️ Configuration (Runtime Tuning)

- `GET /config/schema` – The blueprint: categories, defaults, and metadata
- `GET /config/values` – What's currently configured
- `POST /config/update` – Tweak settings on the fly
- `POST /config/reset` – Back to factory defaults
- `POST /config/optimize` – Let Snappy auto-tune based on your hardware

⚠️ **Remember**: Runtime changes are temporary! Update `.env` for permanent tweaks.

## Chat & Visual Citations 💬

The chat magic happens in the frontend at `frontend/app/api/chat/route.ts`. This Next.js route:
1. Calls the OpenAI Responses API
2. Streams responses via Server-Sent Events
3. Injects beautiful page images through custom `kb.images` events

Snappy's backend? It handles the heavy lifting: document search (`GET /search`) and system maintenance. But it stays out of the chat proxy game; that's the frontend's jam! 🎵

## Configuration UI - Settings Made Simple 🎛️

The `/configuration` page is where you become the maestro! It connects to the `/config/*` API and gives you:
- ✅ Typed inputs with validation
- 📊 Real-time updates
- 💾 Draft detection (when browser and server disagree)
- ♻️ Smart cache invalidation (critical changes refresh services automatically)

No restarts, no yaml wrestling, no config file archaeology. Just smooth, intuitive tuning! 🎶
