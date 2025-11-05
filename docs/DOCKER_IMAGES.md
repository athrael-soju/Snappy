# Using Pre-built Docker Images 🐳

Snappy provides pre-built Docker images hosted on GitHub Container Registry (GHCR) for easy deployment without needing to build from source.

---

## 📦 Available Images

All images are available at `ghcr.io/athrael-soju/snappy/`:

| Image | Description | Tags | Platform |
|-------|-------------|------|----------|
| `backend` | FastAPI backend service | `latest`, `v*.*.*`, `main` | `linux/amd64`, `linux/arm64` |
| `frontend` | Next.js frontend application | `latest`, `v*.*.*`, `main` | `linux/amd64`, `linux/arm64` |
| `colpali-cpu` | ColPali embedding service (CPU) | `latest`, `v*.*.*`, `main` | `linux/amd64`, `linux/arm64` |
| `colpali-gpu` | ColPali embedding service (GPU) | `latest`, `v*.*.*`, `main` | `linux/amd64` |

### Optional Services (Build Locally)

The following services are available but not pre-built in the registry. Build them locally from the repository:

| Service | Location | Description | Build Command |
|---------|----------|-------------|---------------|
| `deepseek-ocr` | `deepseek-ocr/` | DeepSeek OCR service for advanced text extraction | `cd deepseek-ocr && docker compose up --build -d` |

See `deepseek-ocr/README.md` for configuration and usage details.

---

## 🚀 Quick Start with Pre-built Images

### 1. Pull Images

```bash
# Pull all images
docker pull ghcr.io/athrael-soju/snappy/backend:latest
docker pull ghcr.io/athrael-soju/snappy/frontend:latest
docker pull ghcr.io/athrael-soju/snappy/colpali-cpu:latest

# Or pull specific version
docker pull ghcr.io/athrael-soju/snappy/backend:v0.2.0
```

### 2. Create docker-compose.yml

Create a minimal `docker-compose.yml` for production deployment:

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/athrael-soju/snappy/backend:latest
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - MINIO_URL=minio:9000
      - COLPALI_URL=http://colpali:7000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - qdrant
      - minio
      - colpali
    restart: unless-stopped

  frontend:
    image: ghcr.io/athrael-soju/snappy/frontend:latest
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - backend
    restart: unless-stopped

  colpali:
    image: ghcr.io/athrael-soju/snappy/colpali-cpu:latest
    ports:
      - "7000:7000"
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    restart: unless-stopped

volumes:
  qdrant_data:
  minio_data:
```

### Optional: Adding DeepSeek OCR Service

To include the DeepSeek OCR service for advanced text extraction, add this to your `docker-compose.yml`:

```yaml
services:
  # ... existing services (backend, frontend, colpali, qdrant, minio) ...

  deepseek-ocr:
    build: ./deepseek-ocr  # Build locally (not in GHCR)
    container_name: deepseek-ocr
    ports:
      - "8200:8200"
    environment:
      - MODEL_NAME=deepseek-ai/DeepSeek-OCR
      - API_HOST=0.0.0.0
      - API_PORT=8200
    volumes:
      - deepseek_models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    shm_size: "4g"
    restart: unless-stopped

volumes:
  qdrant_data:
  minio_data:
  deepseek_models:
```

Enable OCR in the backend by adding to your `.env`:
```bash
DEEPSEEK_OCR_ENABLED=True
DEEPSEEK_OCR_URL=http://deepseek-ocr:8200
```

See `deepseek-ocr/README.md` for detailed configuration options.

---

```bash
# Create .env file with your secrets
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### 4. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **MinIO Console**: http://localhost:9001

---

## 🏷️ Image Tags

### Semantic Versioning

Images are tagged with semantic versions on each release:

```bash
# Latest stable release
docker pull ghcr.io/athrael-soju/snappy/backend:latest

# Specific version (recommended for production)
docker pull ghcr.io/athrael-soju/snappy/backend:v0.2.0

# Major.minor version (gets latest patch)
docker pull ghcr.io/athrael-soju/snappy/backend:v0.2

# Major version (gets latest minor.patch)
docker pull ghcr.io/athrael-soju/snappy/backend:v0
```

### Development Tags

```bash
# Latest from main branch (unstable)
docker pull ghcr.io/athrael-soju/snappy/backend:main

# Specific commit SHA
docker pull ghcr.io/athrael-soju/snappy/backend:sha-a1b2c3d
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file with required configuration:

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-your-key-here

# Qdrant (Optional - defaults shown)
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=colpali_documents

# MinIO (Optional - defaults shown)
MINIO_URL=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# ColPali (Optional - defaults shown)
COLPALI_URL=http://colpali:7000
COLPALI_API_TIMEOUT=300

# Backend (Optional)
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000
```

### Volume Mounts

For persistent data, mount volumes:

```yaml
services:
  backend:
    image: ghcr.io/athrael-soju/snappy/backend:latest
    volumes:
      # Mount custom config (optional)
      - ./my-config.env:/app/.env
```

---

## 🎯 Production Deployment Examples

### Using GPU for ColPali

```yaml
services:
  colpali:
    image: ghcr.io/athrael-soju/snappy/colpali-gpu:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

### Behind a Reverse Proxy (nginx)

```yaml
services:
  frontend:
    image: ghcr.io/athrael-soju/snappy/frontend:latest
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
    expose:
      - "3000"
    restart: unless-stopped

  backend:
    image: ghcr.io/athrael-soju/snappy/backend:latest
    environment:
      - ALLOWED_ORIGINS=https://yourdomain.com
    expose:
      - "8000"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### Scaling Services

```yaml
services:
  backend:
    image: ghcr.io/athrael-soju/snappy/backend:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## 🔄 Updating Images

### Check for Updates

```bash
# Pull latest version
docker pull ghcr.io/athrael-soju/snappy/backend:latest

# Check image details
docker images ghcr.io/athrael-soju/snappy/backend
```

### Update Running Services

```bash
# Pull new images
docker compose pull

# Restart services with new images
docker compose up -d

# Remove old images
docker image prune
```

### Rollback to Previous Version

```bash
# Update docker-compose.yml to use specific tag
# Change: backend:latest
# To:     backend:v0.1.0

# Restart services
docker compose up -d
```

---

## 🐛 Troubleshooting

### Image Pull Failures

**Problem**: `Error response from daemon: manifest not found`

**Solution**:
```bash
# Verify image exists
docker manifest inspect ghcr.io/athrael-soju/snappy/backend:latest

# Try specific version tag
docker pull ghcr.io/athrael-soju/snappy/backend:v0.2.0
```

### Authentication Required

**Problem**: `unauthorized: authentication required`

**Solution**:
```bash
# Login to GHCR (for private repositories)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or use personal access token
docker login ghcr.io
```

### Platform Compatibility

**Problem**: `no matching manifest for linux/arm64`

**Solution**:
```bash
# Force specific platform
docker pull --platform linux/amd64 ghcr.io/athrael-soju/snappy/backend:latest

# Or use CPU image on ARM
docker pull ghcr.io/athrael-soju/snappy/colpali-cpu:latest
```

### Container Health Checks

```bash
# Check container status
docker compose ps

# View container logs
docker compose logs backend

# Inspect container
docker inspect snappy-backend-1
```

---

## 📊 Image Information

### View Image Metadata

```bash
# Inspect image
docker inspect ghcr.io/athrael-soju/snappy/backend:latest

# View image layers
docker history ghcr.io/athrael-soju/snappy/backend:latest

# Check image size
docker images ghcr.io/athrael-soju/snappy/backend
```

### Security Scanning

```bash
# Scan for vulnerabilities (using Docker Scout)
docker scout cves ghcr.io/athrael-soju/snappy/backend:latest

# Or use Trivy
trivy image ghcr.io/athrael-soju/snappy/backend:latest
```

---

## 🔗 Related Resources

- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Project README](../README.md)
- [Configuration Guide](../backend/docs/configuration.md)

---

## 💡 Best Practices

1. **Pin versions in production**: Use specific version tags (`v0.2.0`) instead of `latest`
2. **Use multi-stage builds**: Images are optimized for size and security
3. **Scan regularly**: Run security scans on images before deployment
4. **Update frequently**: Pull new images regularly for security patches
5. **Monitor resources**: Set appropriate CPU/memory limits
6. **Use health checks**: Implement container health checks
7. **Backup data**: Regularly backup Qdrant and MinIO volumes

---

**Last Updated:** November 4, 2025  
**Registry:** GitHub Container Registry (GHCR)
