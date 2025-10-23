# Contributing to Snappy 🤝

Thank you for your interest in contributing to Snappy! We welcome contributions from the community and are excited to have you here.

This guide will help you get started, understand our development workflow, and make meaningful contributions to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone, regardless of background or identity. We expect all contributors to:

- Be respectful and considerate
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Accept responsibility and apologize when mistakes happen
- Prioritize what's best for the community

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory remarks
- Public or private harassment
- Publishing others' private information without permission
- Unprofessional or unwelcome conduct

### Enforcement

Project maintainers have the right to remove, edit, or reject contributions that violate this Code of Conduct. Report unacceptable behavior to the project maintainers.

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Git** installed and configured
- **Docker & Docker Compose** for running services
- **Python 3.11+** with `uv` package manager (for backend)
- **Node.js 18+** with `yarn` (for frontend)
- **WSL** (Windows Subsystem for Linux) if on Windows
- **CUDA toolkit** (optional, for GPU-accelerated ColPali)

### First-Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/athrael.soju/Snappy.git
   cd Snappy
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/athrael-soju/Snappy.git
   ```

4. **Review the documentation**:
   - `README.md` - Project overview
   - `AGENTS.md` - Comprehensive development guide
   - `VERSIONING.md` - Version management
   - `backend/docs/` - Architecture and configuration
   - `frontend/README.md` - Frontend-specific docs

---

## Development Setup

### Backend Setup (WSL Terminal)

```bash
# Navigate to backend
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Copy environment file
cp ../.env.example ../.env
# Edit .env with your configuration

# Run backend
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup (Bash/PowerShell Terminal)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
yarn install --frozen-lockfile

# Copy environment file
cp .env.example .env.local
# Add your OPENAI_API_KEY to .env.local

# Run frontend
yarn dev
```

### ColPali Service Setup (WSL Terminal)

```bash
# Navigate to ColPali directory
cd colpali

# Start with Docker (choose one profile)
# GPU
docker compose --profile gpu up -d --build

# OR CPU
docker compose --profile cpu up -d --build
```

### Infrastructure Services

Start Qdrant and MinIO:

```bash
# From project root
docker compose up -d qdrant minio
```

Or run the entire stack:

```bash
docker compose up -d --build
```

---

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes** - Fix issues and improve stability
- ✨ **Features** - Add new functionality
- 📚 **Documentation** - Improve docs, add examples
- 🎨 **UI/UX** - Enhance user interface and experience
- ⚡ **Performance** - Optimize speed and efficiency
- 🧪 **Tests** - Add or improve test coverage
- 🔧 **Tooling** - Improve development tools and scripts

### Finding Issues to Work On

- Check the [GitHub Issues](https://github.com/athrael-soju/Snappy/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on an issue to express interest before starting work
- Ask questions if anything is unclear

### Creating New Issues

Before creating an issue:

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide context**: 
   - Clear description of the problem/feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Screenshots/logs if applicable
   - Your environment (OS, Python version, Node version)

---

## Coding Standards

### General Principles

- **Follow existing patterns** in the codebase
- **DRY (Don't Repeat Yourself)** - Reuse code when possible
- **KISS (Keep It Simple, Stupid)** - Favor simplicity over complexity
- **Single Responsibility** - Each function/class should do one thing well
- **Clear naming** - Use descriptive names over comments

### Backend (Python)

**Style:**
- Follow [PEP 8](https://pep8.org/) style guide
- Use `black` for formatting (enforced by pre-commit)
- Use `isort` for import sorting
- Maximum line length: 88 characters (black default)

**Type Hints:**
- **Required** for all function signatures
- Use built-in types where possible (`list`, `dict`, `tuple`)
- Use `typing` module for complex types
- Pyright enforces type checking

**Example:**
```python
from typing import List, Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    k: int = 10
    collection: Optional[str] = None

async def search_documents(
    request: SearchRequest,
    service: QdrantService
) -> List[SearchResult]:
    """Search documents using visual embeddings.
    
    Args:
        request: Search parameters
        service: Qdrant service instance
        
    Returns:
        List of search results with scores and metadata
    """
    results = await service.search(request.query, request.k)
    return results
```

**Async/Await:**
- Use `async`/`await` for I/O operations
- Never use blocking calls in async functions
- Use `asyncio` primitives for concurrency

**Error Handling:**
```python
from fastapi import HTTPException

try:
    result = await service.operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Frontend (TypeScript)

**Style:**
- Follow TypeScript strict mode conventions
- Use Prettier for formatting (configured in project)
- Prefer functional components over class components
- Use meaningful component and variable names

**Type Safety:**
- **No `any` types** - Use `unknown` if type is uncertain
- Leverage generated types from OpenAPI spec
- Use Zod for runtime validation

**Example:**
```typescript
import { SearchRequestSchema } from '@/lib/validation/schemas';
import { apiClient } from '@/lib/api/client';
import type { SearchResult } from '@/types/api';

interface SearchProps {
  query: string;
  limit?: number;
}

export async function searchDocuments({ 
  query, 
  limit = 10 
}: SearchProps): Promise<SearchResult[]> {
  // Runtime validation
  const validated = SearchRequestSchema.parse({ query, k: limit });
  
  // Type-safe API call
  const response = await apiClient.get('/search', {
    params: validated
  });
  
  return response.data;
}
```

**React Best Practices:**
- Server Components by default
- Client Components only when needed (`'use client'`)
- Use hooks appropriately (`useState`, `useEffect`, `useMemo`)
- Memoize expensive computations
- Extract reusable logic into custom hooks

**Component Structure:**
```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

interface ComponentProps {
  title: string;
  onSubmit: (value: string) => void;
}

export function MyComponent({ title, onSubmit }: ComponentProps) {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    if (value.trim()) {
      onSubmit(value);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-heading-2">{title}</h2>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="input"
      />
      <Button onClick={handleSubmit}>Submit</Button>
    </div>
  );
}
```

### Architecture Patterns

**Backend Structure:**
```
Routers (HTTP handlers)
    ↓
Dependencies (service instances)
    ↓
Services (business logic)
    ↓
External APIs/DBs
```

**When adding features:**

1. **New endpoint?** → Add router in `backend/api/routers/`
2. **Business logic?** → Create/extend service in `backend/services/`
3. **New config?** → Add to `backend/config_schema.py`
4. **Long-running task?** → Use `BackgroundTasks` + progress tracking
5. **UI needed?** → Create page in `frontend/app/` or component in `frontend/components/`

---

## Commit Guidelines

We use **Conventional Commits** for all commits. This enables automated versioning and changelog generation.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor (0.X.0) |
| `fix` | Bug fix | Patch (0.0.X) |
| `feat!` or `fix!` | Breaking change | Major (X.0.0) |
| `docs` | Documentation only | None |
| `style` | Code formatting | None |
| `refactor` | Code restructuring | None |
| `perf` | Performance improvements | Patch |
| `test` | Adding tests | None |
| `build` | Build system changes | None |
| `ci` | CI/CD changes | None |
| `chore` | Maintenance tasks | None |

### Examples

```bash
# Feature (minor version bump)
git commit -m "feat: add visual similarity search"

# Bug fix (patch version bump)
git commit -m "fix: resolve embedding dimension mismatch"

# Breaking change (major version bump)
git commit -m "feat!: redesign search API

BREAKING CHANGE: /search endpoint now requires 'collection' parameter"

# Documentation (no version bump)
git commit -m "docs: update configuration guide"

# Multiple changes
git commit -m "feat: add MUVERA support

- Implement first-stage retrieval
- Add configuration options
- Update search flow"
```

### Commit Best Practices

- **Keep commits atomic** - One logical change per commit
- **Write clear messages** - Describe what and why, not how
- **Reference issues** - Use `Closes #123` in commit footer
- **Test before committing** - Ensure code works
- **Run pre-commit hooks** - Formatting and linting checks

---

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   # Backend (WSL)
   cd backend
   pre-commit run --all-files
   
   # Frontend (bash)
   cd frontend
   yarn type-check
   yarn build
   ```

3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Regenerate types** if API changed:
   ```bash
   # WSL (from project root)
   uv run python scripts/generate_openapi.py
   
   # bash
   cd frontend
   yarn gen:sdk
   yarn gen:zod
   ```

### Creating the PR

1. **Push to your fork**:
   ```bash
   git push origin your-feature-branch
   ```

2. **Open PR on GitHub** against `main` branch

3. **Fill out PR template** with:
   - Clear description of changes
   - Related issue numbers (e.g., `Closes #123`)
   - Screenshots/videos for UI changes
   - Breaking changes (if any)
   - Testing performed

4. **Use descriptive title** following conventional commit format:
   ```
   feat: add visual similarity search
   fix: resolve MinIO connection timeout
   ```

### PR Review Process

- Maintainers will review within 3-5 business days
- Address feedback by pushing new commits
- Engage respectfully in discussions
- Be patient and open to suggestions

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commits follow conventional format
- [ ] Types regenerated if API changed
- [ ] Pre-commit hooks pass

### After Merge

- Your changes will be included in the next release
- Release Please will automatically version and changelog
- Delete your feature branch
- Update your fork:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

---

## Testing

### Backend Testing

**Run tests:**
```bash
cd backend
uv run pytest tests/
```

**Manual API testing:**
```bash
# Health check
curl http://localhost:8000/health

# Search
curl "http://localhost:8000/search?q=test&k=5"

# Upload
curl -X POST http://localhost:8000/index \
  -F "files=@/path/to/document.pdf"
```

**Test coverage:**
```bash
uv run pytest --cov=backend tests/
```

### Frontend Testing

**Type checking:**
```bash
cd frontend
yarn type-check
```

**Build validation:**
```bash
yarn build
yarn start
```

**Component testing:**
```bash
yarn test  # If tests are configured
```

### Integration Testing

1. Start all services via Docker Compose
2. Test full workflow: upload → indexing → search → chat
3. Monitor logs for errors:
   ```bash
   docker compose logs -f backend
   ```
4. Check Qdrant UI: http://localhost:6333/dashboard
5. Check MinIO console: http://localhost:9001

### Writing Tests

**Backend:**
```python
import pytest
from backend.services.qdrant.search import normalize_scores

def test_normalize_scores():
    scores = [10.0, 5.0, 2.5]
    normalized = normalize_scores(scores)
    
    assert normalized[0] == 1.0  # Max score normalized to 1
    assert 0 <= normalized[-1] <= 1  # All scores in range
    assert len(normalized) == len(scores)
```

**Frontend:**
```typescript
import { render, screen } from '@testing-library/react';
import { SearchComponent } from '@/components/search';

test('renders search input', () => {
  render(<SearchComponent />);
  const input = screen.getByPlaceholderText(/search/i);
  expect(input).toBeInTheDocument();
});
```

---

## Documentation

### What to Document

- **New features** - Explain what it does and how to use it
- **Configuration changes** - Update `backend/docs/configuration.md`
- **API changes** - Regenerate OpenAPI spec
- **Breaking changes** - Document migration steps
- **Architecture decisions** - Update `backend/docs/architecture.md`

### Documentation Standards

**Code Comments:**
```python
def complex_function(param: str) -> dict:
    """Brief description of function.
    
    Longer explanation if needed. Describe edge cases,
    assumptions, or important implementation details.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param is invalid
    """
```

**README Updates:**
- Keep examples concise and working
- Update table of contents
- Add links to related documentation
- Use screenshots for UI changes

**API Documentation:**
- Use clear endpoint descriptions
- Document all parameters and responses
- Provide example requests/responses
- Note any authentication requirements

### Generating Documentation

**OpenAPI spec:**
```bash
# WSL (from project root)
uv run python scripts/generate_openapi.py
```

**Frontend types:**
```bash
cd frontend
yarn gen:sdk    # TypeScript types
yarn gen:zod    # Zod schemas
```

---

## Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **GitHub Issues** - Report bugs, request features
- **Documentation** - Check `AGENTS.md`, `README.md`, and `backend/docs/`

### Staying Updated

- **Watch the repository** for notifications
- **Star the project** to show support
- **Follow releases** for new versions

### Recognition

Contributors are recognized in:
- Release notes and changelogs
- README contributors section
- GitHub insights and graphs

---

## Additional Resources

### Documentation
- [Project README](README.md)
- [AI Agent Guide](AGENTS.md)
- [Version Management](VERSIONING.md)
- [Backend Architecture](backend/docs/architecture.md)
- [Configuration Guide](backend/docs/configuration.md)

### External References
- [Conventional Commits](https://www.conventionalcommits.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [ColPali Paper](https://arxiv.org/abs/2407.01449)

### Tools & Technologies
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Release Please](https://github.com/googleapis/release-please)
- [Pyright](https://github.com/microsoft/pyright)
- [shadcn/ui](https://ui.shadcn.com/)

---

## Questions?

If you have questions not covered in this guide:

1. Check the [documentation](README.md)
2. Search [existing issues](https://github.com/athrael-soju/Snappy/issues)
3. Ask in [GitHub Discussions](https://github.com/athrael-soju/Snappy/discussions)
4. Open a new issue

---

## Thank You! 🙏

Every contribution, no matter how small, makes Snappy better. We appreciate your time and effort in helping improve this project.

Happy coding! 🚀

---

**Last Updated:** October 23, 2025  
**License:** [MIT](LICENSE)
