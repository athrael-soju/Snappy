# ColQwen2.5 FastAPI Service

A FastAPI-based service for generating embeddings from images and text queries using the ColQwen2.5 model.

## Features

- 🖼️ **Image Embeddings**: Generate embeddings for images
- 🔤 **Text Embeddings**: Generate embeddings for text queries
- 🚀 **High Performance**: Utilizes Flash Attention 2 when available
- 📊 **RESTful API**: Easy integration with other services
- 🏥 **Health Monitoring**: Built-in health and info endpoints
- 📏 **Patch Calculation**: Utility endpoint for patch calculations
- 🔄 **Batch Processing**: Support for processing multiple images/queries in a single request

## Prerequisites

- Python 3.10+
- CUDA-compatible GPU (recommended)
- PyTorch with CUDA support
- [Flash Attention 2](https://github.com/Dao-AILab/flash-attention) (optional, for better performance)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/athrael-soju/colpali-template.git
   cd colpali-template/colpali
   ```
2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Install Flash Attention 2 (optional, for better performance):

   ```bash
   pip install flash-attn --no-build-isolation
   ```

## Usage

### Starting the Server

```bash
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

### Docker

Run with Docker Compose (recommended):

```bash
# CPU service on http://localhost:7001
docker compose up -d api-cpu

# GPU service on http://localhost:7002 (requires NVIDIA Container Toolkit)
docker compose up -d api-gpu
```

Notes:

- Images are built from `Dockerfile.cpu` and `Dockerfile.gpu`.
- The Hugging Face cache is persisted in a named volume `hf-cache` at `/data/hf-cache`.
- GPU service requires recent NVIDIA drivers and Docker `--gpus` support.

#### Build images

- Standard docker build:
  ```bash
  docker build -f Dockerfile.cpu -t colqwen-api-cpu .
  docker build -f Dockerfile.gpu -t colqwen-api-gpu .
  ```
- Or with Docker Compose:
  ```bash
  docker compose build
  ```

### API Endpoints

#### Root Endpoint

- `GET /`: Returns API name and version
  ```json
  {
    "message": "ColQwen2.5 Embedding API",
    "version": "0.0.2"
  }
  ```

#### Health Check

- `GET /health`: Health check endpoint
  ```json
  {
    "status": "healthy",
    "device": "cuda:0"
  }
  ```

#### Service Info

- `GET /info`: Get service and model information
  ```json
  {
    "version": "0.0.2",
    "device": "cuda:0",
    "dtype": "torch.bfloat16",
    "flash_attn": true,
    "spatial_merge_size": 2,
    "dim": 1536,
    "image_token_id": 151655
  }
  ```

#### Patch Calculation

- `POST /patches`: Calculate number of patches for given image dimensions (batch)
  **Request Body**:

  ```json
  {
    "dimensions": [
      { "width": 1024, "height": 768 },
      { "width": 512,  "height": 512 }
    ]
  }
  ```

  **Response**:
  ```json
  {
    "results": [
      { "width": 1024, "height": 768, "n_patches_x": 32, "n_patches_y": 24 },
      { "width": 512,  "height": 512, "n_patches_x": 16, "n_patches_y": 16 }
    ]
  }
  ```

#### Text Embeddings

- `POST /embed/queries`: Generate embeddings for text queries
  **Request Body**:

  ```json
  {
    "queries": ["a photo of a cat", "a photo of a dog"]
  }
  ```

  **Response**:
  ```json
  {
    "embeddings": [
      [[0.1, 0.2, ...], ...],
      [[0.3, 0.4, ...], ...]
    ]
  }
  ```

  Notes:- `queries` may be a single string or a list of strings.
  - Shape per item is `[sequence_length, hidden_dim]`.

#### Image Embeddings

- `POST /embed/images`: Generate embeddings for uploaded images
  **Request**: `multipart/form-data` with image files
  **Response**:
  ```json
  {
    "embeddings": [
      {
        "embedding": [[0.1, 0.2, ...], ...],
        "image_patch_start": 128,
        "image_patch_len": 256
      }
    ]
  }
  ```

  Notes:- For each image, the response includes the embedding matrix and the image-token span within the sequence.

## Error Handling

The API returns appropriate HTTP status codes and error messages in JSON format:

- `400 Bad Request`: Invalid input parameters
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

## Development

To run the development server with auto-reload:

```bash
uvicorn app:app --reload
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Model Information

This service uses the `vidore/colqwen2.5-v0.2` model (ColQwen2.5 architecture) via `colpali_engine`.
See `GET /info` for runtime details like device, dtype, and model token ids.

### Example Requests

#### Get Embeddings for Text Queries

```bash
curl -X POST "http://localhost:7000/embed/queries" \
     -H "Content-Type: application/json" \
     -d '{"queries": ["example query"]}'
```

#### Get Embeddings for Images

```bash
curl -X POST "http://localhost:7000/embed/images" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@image1.jpg" \
     -F "files=@image2.jpg"
```

If running with Docker Compose, replace `7000` with `7001` (CPU) or `7002` (GPU).

## API Documentation

### Interactive Documentation

Once the server is running, visit `http://localhost:7000/docs` for interactive API documentation powered by Swagger UI.

### Generating OpenAPI Specification

To generate the OpenAPI specification file (`openapi.json`), run:

```bash
python generate_openapi.py
```

This will create an `openapi.json` file in the project root containing the complete API specification. You can use this file for:

- API client generation
- Documentation generation
- Importing into API testing tools
- Version control of your API contract

The OpenAPI spec is automatically generated from your FastAPI application's route definitions and type hints, ensuring it stays in sync with your code.

## Configuration

The service automatically uses GPU if available. To force CPU usage or configure other settings, modify the model loading parameters in `app.py`.
