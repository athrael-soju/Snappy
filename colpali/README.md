# ColPali Embedding API - The Vision Brain! 🧠✨

This is where the visual understanding magic happens! Our FastAPI service serves up query and image embeddings using the powerful ColQwen2.5 model, complete with image-token boundary metadata.

- **App**: `colpali/app.py`
- **Ports**: Listens on 7000 in-container
  - 🖥️ CPU mode → `localhost:7001`
  - 🚀 GPU mode → `localhost:7002`
- **Model**: `vidore/colqwen2.5-v0.2` (state-of-the-art vision-language model!)

## API Endpoints 🎯
- `GET /health` - Check if we're alive and which device we're running on
- `GET /info` - Device info, data type, dimensions, and `image_token_id`
- `POST /patches` - Calculate patch grids (`n_patches_x/y`) for your images
- `POST /embed/queries` - Turn text queries into embeddings
- `POST /embed/images` - Transform images into embeddings (with patch boundaries!)

## Docker Compose - The Easy Way! 🐳

```bash
# From the colpali/ directory

# CPU Mode (everyone can use this!)
docker compose up -d api-cpu
# → Available at http://localhost:7001

# GPU Mode (requires NVIDIA runtime - FAST!)
docker compose up -d api-gpu
# → Available at http://localhost:7002
```

**Smart Caching** 💾: We use a named volume (`hf-cache`) to persist your Hugging Face model downloads at `/data/hf-cache`. Download once, use forever!

## Connect Snappy to ColPali 🔌

In your root `.env` file (the backend reads this):
```bash
# Choose your fighter: cpu or gpu
COLPALI_MODE=cpu

# Tell Snappy where to find the services
COLPALI_CPU_URL=http://localhost:7001
COLPALI_GPU_URL=http://localhost:7002
```

Snappy's backend will automatically pick the right URL based on your `COLPALI_MODE` setting. Easy! 🎉

## Running Locally (No Docker) 💻

```bash
# From the colpali/ directory

# Set up your virtual environment
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -U pip setuptools wheel
pip install -r requirements.txt

# Fire it up!
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

**Access Points**:
- 🏠 Local direct: http://localhost:7000
- 🐳 Docker Compose style: http://localhost:7001 (CPU) or :7002 (GPU)

## Good to Know 📝
- **Model Access**: ColQwen2.5 is public, but it's a big download! First run might take a minute.
- **GPU Requirements**: Need NVIDIA Container Toolkit for GPU mode (worth it for the speed!)
- **Gated Models**: If you switch to a gated model, authenticate with Hugging Face first

## How It All Connects 🔗

This embedding service is Snappy's visual brain:
1. 🧠 Provides query & image embeddings to the backend
2. 🔍 Powers the search functionality (`GET /search`)
3. 💬 Enables the chat route to find relevant document pages
4. ✨ Makes visual citations possible!

When the Next.js chat route finds relevant images, it emits a `kb.images` Server-Sent Event, and the UI lights up with that beautiful "Visual citations included" chip and image gallery. It's all connected! 🎭
