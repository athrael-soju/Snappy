# Project Scripts

Utility scripts for Snappy.

## generate_openapi.py
Generate backend OpenAPI JSON (default: `frontend/docs/openapi.json`).
```bash
uv run python scripts/generate_openapi.py [--out path/to/openapi.json]
```
Run after API changes; then run `yarn gen:sdk` and `yarn gen:zod` in `frontend`.

## sync_version.py
Check or set versions across frontend/backend and release manifest.
```bash
python scripts/sync_version.py          # check
python scripts/sync_version.py 1.2.3    # set
```

## create_release.sh
Interactive helper for releases.
```bash
./scripts/create_release.sh
```
