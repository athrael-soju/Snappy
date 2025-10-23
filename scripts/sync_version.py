#!/usr/bin/env python3
"""
Sync version between frontend package.json and backend __version__.py
This script ensures version consistency across the entire stack.

Usage:
    python scripts/sync_version.py [version]

    If version is not provided, reads from package.json
"""

import json
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def read_frontend_version() -> str:
    """Read version from frontend package.json."""
    package_json_path = get_project_root() / "frontend" / "package.json"

    if not package_json_path.exists():
        raise FileNotFoundError(f"package.json not found at {package_json_path}")

    with open(package_json_path, "r") as f:
        data = json.load(f)

    return data.get("version", "0.0.0")


def read_backend_version() -> str:
    """Read version from backend __version__.py."""
    version_path = get_project_root() / "backend" / "__version__.py"

    if not version_path.exists():
        raise FileNotFoundError(f"__version__.py not found at {version_path}")

    with open(version_path, "r") as f:
        content = f.read()

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)

    raise ValueError("Could not find __version__ in __version__.py")


def update_frontend_version(version: str) -> None:
    """Update version in frontend package.json."""
    package_json_path = get_project_root() / "frontend" / "package.json"

    with open(package_json_path, "r") as f:
        data = json.load(f)

    data["version"] = version

    with open(package_json_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")  # Add trailing newline

    print(f"✓ Updated frontend/package.json to version {version}")


def update_backend_version(version: str) -> None:
    """Update version in backend __version__.py."""
    version_path = get_project_root() / "backend" / "__version__.py"

    content = (
        f'"""Version information for Snappy backend."""\n\n__version__ = "{version}"\n'
    )

    with open(version_path, "w") as f:
        f.write(content)

    print(f"✓ Updated backend/__version__.py to version {version}")


def update_release_manifest(version: str) -> None:
    """Update .release-please-manifest.json."""
    manifest_path = get_project_root() / ".release-please-manifest.json"

    data = {".": version}

    with open(manifest_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"✓ Updated .release-please-manifest.json to version {version}")


def validate_version(version: str) -> bool:
    """Validate semantic version format."""
    pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
    return bool(re.match(pattern, version))


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Version provided as argument
        new_version = sys.argv[1]

        if not validate_version(new_version):
            print(f"❌ Invalid version format: {new_version}")
            print("   Expected format: X.Y.Z or X.Y.Z-prerelease+build")
            sys.exit(1)

        print(f"Setting version to {new_version}...")
        update_frontend_version(new_version)
        update_backend_version(new_version)
        update_release_manifest(new_version)
        print(f"\n✅ All versions synced to {new_version}")
    else:
        # No argument, show current versions
        try:
            frontend_version = read_frontend_version()
            backend_version = read_backend_version()

            print("Current versions:")
            print(f"  Frontend: {frontend_version}")
            print(f"  Backend:  {backend_version}")

            if frontend_version != backend_version:
                print("\n⚠️  Versions are out of sync!")
                print(f"   Run: python scripts/sync_version.py {frontend_version}")
                sys.exit(1)
            else:
                print("\n✅ Versions are in sync")
        except Exception as e:
            print(f"❌ Error reading versions: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
