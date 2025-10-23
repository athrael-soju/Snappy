#!/usr/bin/env python
"""
Generate OpenAPI JSON spec for the FastAPI backend.

Usage:
  python scripts/generate_openapi.py [--out <path>]

By default, writes to frontend/docs/openapi.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    # Resolve project structure
    script_path = Path(__file__).resolve()
    # repo root (parent of scripts/)
    project_root = script_path.parent.parent
    # backend/ directory
    backend_path = project_root / "backend"
    # frontend/docs directory
    docs_dir = project_root / "frontend" / "docs"
    # Default output
    docs_default = docs_dir / "openapi.json"

    # Ensure backend is importable so `from api.app import create_app` works
    sys.path.insert(0, str(backend_path))

    # Parse args
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI JSON for FastAPI app"
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=str(docs_default),
        help="Output file path for the OpenAPI JSON (default: frontend/docs/openapi.json)",
    )
    args = parser.parse_args()

    # Import after sys.path adjustment
    try:
        from api.app import create_app  # type: ignore[import-not-found]
    except Exception as e:
        print(f"[ERROR] Failed to import FastAPI app factory: {e}")
        return 1

    try:
        app = create_app()
    except Exception as e:
        print(f"[ERROR] Failed to create FastAPI app: {e}")
        return 1

    # Build the OpenAPI schema
    try:
        schema = app.openapi()
    except Exception as e:
        print(f"[ERROR] Failed to generate OpenAPI schema: {e}")
        return 1

    # Write to file
    out_path = Path(args.out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"[OK] OpenAPI schema written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
