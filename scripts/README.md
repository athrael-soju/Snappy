# Project Scripts 🛠️

This directory contains project-level utility scripts for managing the Snappy codebase.

---

## Available Scripts

### `generate_openapi.py`

Generates the OpenAPI JSON specification from the FastAPI backend.

**Usage:**
```bash
# In WSL (from project root)
uv run python scripts/generate_openapi.py

# Custom output location
uv run python scripts/generate_openapi.py --out path/to/openapi.json
```

**Default output:** `frontend/docs/openapi.json`

**When to use:**
- After adding/modifying API endpoints
- Before running `yarn gen:sdk` or `yarn gen:zod` in the frontend
- To update the API documentation

---

### `sync_version.py`

Synchronizes version numbers across frontend and backend.

**Usage:**
```bash
# Check current version sync status
python scripts/sync_version.py

# Set a specific version across all files
python scripts/sync_version.py 1.2.3
```

**Files updated:**
- `frontend/package.json`
- `backend/__version__.py`
- `.release-please-manifest.json`

**When to use:**
- Before creating a release
- When versions get out of sync
- To verify version consistency

---

### `create_release.sh`

Interactive script to help create a new release.

**Usage:**
```bash
# In bash terminal
./scripts/create_release.sh
```

**What it does:**
- Shows current version
- Displays recent commits
- Guides you through the release process
- Pushes to GitHub to trigger Release Please

**When to use:**
- When ready to create a new release
- To preview what commits will be included

---

## Workflow Integration

### API Changes → Frontend Types

```bash
# 1. Generate OpenAPI spec (WSL)
uv run python scripts/generate_openapi.py

# 2. Generate TypeScript types (bash)
cd frontend
yarn gen:sdk
yarn gen:zod
```

### Version Management

```bash
# Check sync
python scripts/sync_version.py

# Make commits with conventional format
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"

# Create release
./scripts/create_release.sh
```

---

## Script Requirements

### Python Scripts
- Python 3.10+
- Run with `uv` from project root
- Backend dependencies must be installed

### Bash Scripts
- Git repository
- Node.js (for version checking)
- Conventional commit format for releases

---

## See Also

- `VERSIONING.md` - Complete version management guide
- `AGENTS.md` - Comprehensive developer guide
- `backend/scripts/README.md` - Backend-specific scripts (deprecated)
