# Publishing Docker Images to GitHub Container Registry

This guide explains how Docker images are automatically built and published to GitHub Container Registry (GHCR).

---

## How It Works

The `.github/workflows/docker-publish.yml` workflow automatically:

1. **Builds Docker images** for all components (backend, frontend, colpali-cpu, colpali-gpu, deepseek-ocr, duckdb)
2. **Publishes to GHCR** at `ghcr.io/athrael-soju/snappy/`
3. **Tags images** with multiple tags for flexibility
4. **Supports multi-platform** builds (amd64 and arm64 where applicable)

---

## Triggers

Images are built and published when:

- **Push to main branch** - Creates `latest` and `main` tags
- **New release tag** (`v*.*.*`) - Creates versioned tags (`v0.2.0`, `v0.2`, `v0`)
- **Pull request** - Builds but doesn't publish (validation only)
- **Manual trigger** - Via GitHub Actions UI

---

## Image Tags

Each push creates multiple tags automatically:

### On Release (e.g., `v0.2.0`)
- `v0.2.0` - Exact version
- `v0.2` - Minor version (gets updated with patches)
- `v0` - Major version (gets updated with minor/patch)
- `latest` - Latest stable release
- `sha-a1b2c3d` - Specific commit SHA

### On Main Branch Push
- `main` - Latest development build
- `sha-a1b2c3d` - Specific commit SHA

### On Pull Request
- `pr-123` - Pull request number (not published)

---

## Setting Up GitHub Container Registry

### 1. Enable Package Permissions

The workflow uses `GITHUB_TOKEN` which is automatically provided. No manual setup required!

### 2. Make Packages Public (Optional)

After the first build, packages are private by default. To make them public:

1. Go to https://github.com/users/athrael-soju/packages
2. Click on a package (e.g., `backend`)
3. Click "Package settings"
4. Scroll to "Danger Zone"
5. Click "Change visibility" → "Public"
6. Repeat for all packages

### 3. Verify Package Settings

Ensure each package has:
- ✅ Public visibility (if you want users to pull without authentication)
- ✅ Link to repository (should be automatic)
- ✅ README displayed (inherited from repo)

---

## Manual Workflow Trigger

To manually trigger a build:

1. Go to [Actions tab](https://github.com/athrael-soju/snappy/actions)
2. Click "Docker Build and Publish"
3. Click "Run workflow"
4. Select branch (usually `main`)
5. Click "Run workflow"

---

## Verifying Published Images

### Check Package Registry

Visit: https://github.com/athrael-soju/packages

You should see:
- `backend`
- `frontend`
- `colpali-cpu`
- `colpali-gpu`
- `deepseek-ocr`
- `duckdb`

### Pull and Test Locally

```bash
# Pull an image
docker pull ghcr.io/athrael-soju/snappy/backend:latest

# Run it
docker run -p 8000:8000 ghcr.io/athrael-soju/snappy/backend:latest

# Check it works
curl http://localhost:8000/health
```

---

## Troubleshooting

### Build Failing

**Check workflow logs:**
1. Go to [Actions](https://github.com/athrael-soju/snappy/actions)
2. Click on failed workflow run
3. Expand failed job to see error

**Common issues:**
- Dockerfile syntax errors
- Missing dependencies in requirements.txt
- Build context issues (wrong paths)

### Images Not Publishing

**Verify permissions:**
```yaml
permissions:
  contents: read
  packages: write  # Required for GHCR
  id-token: write
```

**Check if running on PR:**
- Images are built but NOT published on pull requests (by design)
- Only pushes to main and tags publish images

### Authentication Issues

**For public images:**
- No authentication needed to pull
- Users can pull with: `docker pull ghcr.io/...`

**For private images:**
```bash
# Create GitHub Personal Access Token with `read:packages` scope
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Then pull
docker pull ghcr.io/athrael-soju/snappy/backend:latest
```

---

## Updating the Workflow

The workflow file is at: `.github/workflows/docker-publish.yml`

### Adding a New Component

To add a new Docker image:

1. **Add new job** in workflow:
```yaml
build-and-push-new-component:
  runs-on: ubuntu-latest
  permissions:
    contents: read
    packages: write
    id-token: write
  steps:
    # ... copy from existing jobs
```

2. **Update environment variables**:
```yaml
env:
  IMAGE_NAME_NEW_COMPONENT: ${{ github.repository }}/new-component
```

3. **Configure build context**:
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./new-component
    file: ./new-component/Dockerfile
```

### Changing Platforms

To change supported platforms:

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

Note: GPU images should stay `linux/amd64` only due to CUDA compatibility.

---

## Best Practices

1. **Version tagging**: Always tag releases with semantic versioning (`v0.2.0`)
2. **Pin versions**: Use specific tags in production, not `latest`
3. **Multi-platform**: Build for multiple platforms when possible
4. **Cache layers**: Workflow uses GitHub Actions cache for faster builds
5. **Security scanning**: Consider adding Trivy or similar scanner
6. **Size optimization**: Use multi-stage builds (already implemented)

---

## Adding Image Badges to README

Add these to your README for image information:

```markdown
[![Backend Image](https://ghcr-badge.egpl.dev/athrael-soju/snappy/backend/latest_tag?trim=major&label=backend)](https://github.com/athrael-soju/snappy/pkgs/container/backend)
[![Backend Size](https://ghcr-badge.egpl.dev/athrael-soju/snappy/backend/size)](https://github.com/athrael-soju/snappy/pkgs/container/backend)
```

---

## Cost Considerations

GitHub Container Registry:
- ✅ **Free** for public repositories
- ✅ **Unlimited** storage for public images
- ✅ **Unlimited** bandwidth for public images
- ⚠️ **Metered** for private repositories (500MB free)

---

## Next Steps

After first successful build:

1. ✅ Verify images appear in [Packages](https://github.com/athrael-soju/packages)
2. ✅ Make packages public (if desired)
3. ✅ Test pulling and running images
4. ✅ Update documentation with actual image URLs
5. ✅ Add image badges to README
6. ✅ Announce availability to users

---

## Related Documentation

- [docs/DOCKER_IMAGES.md](../docs/DOCKER_IMAGES.md) - User guide for pre-built images
- [GitHub Packages Docs](https://docs.github.com/en/packages)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Docker Metadata Action](https://github.com/docker/metadata-action)

---

**Last Updated:** January 12, 2025
