# Version Management Guide 🏷️

Snappy uses an automated, Git-based versioning strategy powered by **Release Please** and **Conventional Commits**. This ensures consistent version numbers across frontend, backend, and GitHub releases.

---

## Quick Start

### View Current Version

**Frontend (About Page):**
Visit `/about` to see the version badge at the bottom of the page.

**Backend API:**
```bash
curl http://localhost:8000/version
```

**Check Sync Status:**
```bash
# In WSL
python scripts/sync_version.py
```

---

## How It Works

### 1. Conventional Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common types:**
- `feat:` - New feature (bumps **minor** version: 0.X.0)
- `fix:` - Bug fix (bumps **patch** version: 0.0.X)
- `feat!:` or `fix!:` - Breaking change (bumps **major** version: X.0.0)
- `docs:` - Documentation only
- `style:` - Code formatting
- `refactor:` - Code restructuring
- `perf:` - Performance improvements
- `test:` - Adding tests
- `build:` - Build system changes
- `ci:` - CI/CD changes
- `chore:` - Maintenance tasks

**Examples:**
```bash
# Minor version bump (0.1.0 → 0.2.0)
git commit -m "feat: add MUVERA support for faster retrieval"

# Patch version bump (0.1.0 → 0.1.1)
git commit -m "fix: resolve MinIO connection timeout issue"

# Major version bump (0.1.0 → 1.0.0)
git commit -m "feat!: redesign search API with breaking changes

BREAKING CHANGE: /search endpoint now requires 'collection' parameter"

# No version bump
git commit -m "docs: update README with deployment instructions"
```

### 2. Automated Releases

When you push to `main`, **Release Please** automatically:

1. **Analyzes commits** since the last release
2. **Determines next version** based on commit types
3. **Creates a Release PR** with:
   - Updated `package.json` version
   - Updated `backend/__version__.py`
   - Generated `CHANGELOG.md`
4. **When you merge the PR**, it:
   - Creates a GitHub release
   - Tags the commit (e.g., `v0.2.0`)
   - Publishes release notes

### 3. Version Synchronization

Versions are kept in sync across:

| Location | File | Purpose |
|----------|------|---------|
| Frontend | `frontend/package.json` | npm package version |
| Backend | `backend/__version__.py` | Python module version |
| Manifest | `.release-please-manifest.json` | Release Please tracking |
| Git Tags | `v0.1.0` | GitHub releases |

---

## Workflows

### Creating a New Release

#### Option 1: Automatic (Recommended)

1. **Make commits using conventional format:**
   ```bash
   git add .
   git commit -m "feat: add visual search filtering"
   git push origin main
   ```

2. **Release Please creates a PR** (automated)
   - Check GitHub for "chore(main): release 0.2.0" PR
   - Review the CHANGELOG and version bumps

3. **Merge the Release PR**
   - GitHub release is created automatically
   - Version tags are pushed

#### Option 2: Using the Helper Script

```bash
# In bash terminal
./scripts/create_release.sh
```

This script:
- Shows current version
- Displays recent commits
- Pushes to GitHub to trigger Release Please

### Manual Version Sync

If versions get out of sync:

```bash
# In WSL
# Set a specific version
python scripts/sync_version.py 1.2.3

# Or check current sync status
python scripts/sync_version.py
```

### Creating Pre-releases

For beta/alpha releases:

```bash
# Use pre-release version in manifest
# Edit .release-please-manifest.json:
{
  ".": "0.2.0-beta.1"
}

# Commit and push
git add .release-please-manifest.json
git commit -m "chore: prepare beta release"
git push origin main
```

---

## Configuration Files

### `.github/workflows/release-please.yml`

GitHub Actions workflow that runs Release Please on every push to `main`.

**Key features:**
- Automatic version bumping
- CHANGELOG generation
- GitHub release creation
- Major/minor version tags (e.g., `v0`, `v0.2`)

### `release-please-config.json`

Release Please configuration:

```json
{
  "packages": {
    ".": {
      "release-type": "node",
      "package-name": "snappy",
      "bump-minor-pre-major": true,
      "extra-files": [
        {
          "type": "plain-text",
          "path": "backend/__version__.py",
          "glob": false
        }
      ]
    }
  }
}
```

**Key settings:**
- `release-type: node` - Uses package.json as primary version source
- `extra-files` - Also updates backend/__version__.py
- `bump-minor-pre-major` - Allows minor bumps before 1.0.0

### `.release-please-manifest.json`

Tracks current version for Release Please:

```json
{
  ".": "0.1.0"
}
```

---

## Version Display

### Frontend

The About page displays the version from `package.json`:

```tsx
import packageJson from "../../package.json"

<span>Version {packageJson.version}</span>
```

### Backend

The `/version` endpoint exposes backend version:

```python
from backend.__version__ import __version__

@router.get("/version")
async def version():
    return {
        "version": __version__,
        "name": "Snappy Backend",
    }
```

**Access:**
```bash
curl http://localhost:8000/version
```

---

## Best Practices

### 1. Always Use Conventional Commits

```bash
# ✅ Good
git commit -m "feat: add binary quantization support"
git commit -m "fix: correct search score normalization"

# ❌ Bad
git commit -m "updated search"
git commit -m "bug fix"
```

### 2. Group Related Changes

```bash
# Make multiple commits for a feature
git commit -m "feat: add MUVERA first-stage retrieval"
git commit -m "docs: document MUVERA configuration"
git commit -m "test: add MUVERA integration tests"
```

### 3. Review Release PRs Carefully

- Check CHANGELOG accuracy
- Verify version bump is correct
- Test the changes before merging

### 4. Keep Versions in Sync

Run the sync check periodically:
```bash
python scripts/sync_version.py
```

### 5. Tag Releases Descriptively

Release Please generates tags like:
- `v0.1.0` - Full version
- `v0.1` - Minor version (latest patch)
- `v0` - Major version (latest minor)

---

## Troubleshooting

### Versions Out of Sync

**Problem:** Frontend and backend versions differ

**Solution:**
```bash
python scripts/sync_version.py 0.2.0
```

### Release Please Not Creating PR

**Possible causes:**
1. No conventional commits since last release
2. Only `chore:` or `docs:` commits (no version bump)
3. Workflow permissions issue

**Solution:**
- Check GitHub Actions logs
- Ensure commits follow conventional format
- Verify workflow has `contents: write` permission

### Wrong Version Bump

**Problem:** Expected minor bump, got patch

**Solution:**
- Use `feat:` for features (minor bump)
- Use `fix:` for fixes (patch bump)
- Review [Conventional Commits spec](https://www.conventionalcommits.org/)

### Manual Release Needed

If automation fails, create manually:

```bash
# Tag and push
git tag v0.2.0
git push origin v0.2.0

# Sync versions
python scripts/sync_version.py 0.2.0

# Update manifest
echo '{".":" 0.2.0"}' > .release-please-manifest.json
git add .release-please-manifest.json
git commit -m "chore: update release manifest"
git push
```

---

## Examples

### Feature Release (0.1.0 → 0.2.0)

```bash
# Add features with conventional commits
git commit -m "feat: add visual similarity search"
git commit -m "feat: implement search result caching"
git push origin main

# Release Please creates PR: "chore(main): release 0.2.0"
# Merge PR → GitHub release created
```

### Bug Fix Release (0.2.0 → 0.2.1)

```bash
git commit -m "fix: resolve embedding dimension mismatch"
git push origin main

# Release Please creates PR: "chore(main): release 0.2.1"
```

### Breaking Change (0.2.1 → 1.0.0)

```bash
git commit -m "feat!: redesign configuration API

BREAKING CHANGE: config endpoints now use /api/v2/config"
git push origin main

# Release Please creates PR: "chore(main): release 1.0.0"
```

---

## Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Release Please Docs](https://github.com/googleapis/release-please)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)

---

**Last Updated:** October 23, 2025
