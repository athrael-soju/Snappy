# Snappy Feature Implementation Plan Template

> **Project:** Snappy – Vision-Grounded Document Retrieval  
> **Stack:** FastAPI Backend + Next.js 15 Frontend + ColPali Embeddings + Qdrant + MinIO  
> **Planning Methodology:** Understand → Clarify → Plan → Implement

---

## Phase 1: Initial Exploration & Understanding

### Your Task (Before Implementation)

Paste your detailed feature description below:

```
[DETAILED FEATURE DESCRIPTION HERE]
```

---

### AI Responsibilities During Exploration

The AI assistant should:

1. **Analyze the existing codebase thoroughly**
   - Review relevant backend routers (`backend/api/routers/`)
   - Examine frontend pages and components (`frontend/app/`, `frontend/components/`)
   - Understand service integrations (ColPali, Qdrant, MinIO, OpenAI)
   - Review configuration schema (`backend/config_schema.py`, `backend/runtime_config.py`)
   - Check existing API patterns and data models

2. **Determine integration points**
   - Backend API endpoints and dependencies
   - Frontend UI components and routing
   - Service layer modifications (if needed)
   - Configuration updates required
   - Database schema or vector store changes

3. **Identify constraints and edge cases**
   - Authentication/authorization requirements
   - Error handling patterns
   - Performance considerations (streaming, background tasks)
   - Docker/deployment impacts
   - TypeScript/Zod schema regeneration needs

4. **List all ambiguities and questions**
   - Unclear requirements or scope boundaries
   - Multiple implementation approaches
   - Integration with existing features (search, chat, indexing, config, maintenance)
   - UI/UX decisions not specified
   - Testing and validation criteria

---

### Clarification Checklist

Before proceeding to planning, ensure these are clear:

- [ ] **Backend changes:** Which routers, services, models are affected?
- [ ] **Frontend changes:** Which pages, components, API routes are affected?
- [ ] **Configuration:** Any new environment variables or runtime settings?
- [ ] **Data flow:** How does data move through the system?
- [ ] **User experience:** What are the specific UI/UX requirements?
- [ ] **Error handling:** What failure modes need coverage?
- [ ] **Performance:** Any specific latency or throughput requirements?
- [ ] **Dependencies:** New packages or service integrations?
- [ ] **Breaking changes:** Will this affect existing functionality?
- [ ] **Testing strategy:** How will this be validated?

---

### Questions from AI

*(AI will populate this section during exploration)*

#### Architecture Questions
- [Question 1]
- [Question 2]
- ...

#### Implementation Questions
- [Question 1]
- [Question 2]
- ...

#### UI/UX Questions
- [Question 1]
- [Question 2]
- ...

#### Integration Questions
- [Question 1]
- [Question 2]
- ...

---

## Phase 2: Plan Creation

> **Trigger this phase after all questions are answered**

---

# Feature Implementation Plan

**Feature Name:** `[TO BE FILLED]`

**Overall Progress:** `0%`

**Last Updated:** `[DATE]`

---

## Implementation Tasks

### 🏗️ Backend Changes

- [ ] 🟥 **Task 1: [Backend Task Name]**
  - [ ] 🟥 Subtask 1.1
  - [ ] 🟥 Subtask 1.2
  - [ ] 🟥 Subtask 1.3

- [ ] 🟥 **Task 2: [Backend Task Name]**
  - [ ] 🟥 Subtask 2.1
  - [ ] 🟥 Subtask 2.2

---

### 🎨 Frontend Changes

- [ ] 🟥 **Task 3: [Frontend Task Name]**
  - [ ] 🟥 Subtask 3.1
  - [ ] 🟥 Subtask 3.2
  - [ ] 🟥 Subtask 3.3

- [ ] 🟥 **Task 4: [Frontend Task Name]**
  - [ ] 🟥 Subtask 4.1
  - [ ] 🟥 Subtask 4.2

---

### 🔌 Service Integration

- [ ] 🟥 **Task 5: [Service Integration Task Name]**
  - [ ] 🟥 Subtask 5.1
  - [ ] 🟥 Subtask 5.2

---

### ⚙️ Configuration & Environment

- [ ] 🟥 **Task 6: [Configuration Task Name]**
  - [ ] 🟥 Subtask 6.1
  - [ ] 🟥 Subtask 6.2

---

### 🐳 Docker & Deployment

- [ ] 🟥 **Task 7: [Docker/Deployment Task Name]**
  - [ ] 🟥 Subtask 7.1
  - [ ] 🟥 Subtask 7.2

---

### ✅ Testing & Validation

- [ ] 🟥 **Task 8: [Testing Task Name]**
  - [ ] 🟥 Subtask 8.1
  - [ ] 🟥 Subtask 8.2

---

### 📚 Documentation

- [ ] 🟥 **Task 9: [Documentation Task Name]**
  - [ ] 🟥 Update README.md (if needed)
  - [ ] 🟥 Update API documentation
  - [ ] 🟥 Update configuration guide
  - [ ] 🟥 Add inline code comments

---

## Implementation Guidelines

### Development Environment

**Backend & ColPali Services (Python):**
- **Use WSL (Windows Subsystem for Linux)** for all backend and ColPali development
- **Use `uv`** as the Python package manager and environment tool
- Run all backend commands in WSL terminal
- Example: `uv pip install -r requirements.txt`, `uv run uvicorn ...`

**Frontend (Next.js/TypeScript):**
- **Use bash terminal** for all frontend development
- Run all Node.js/npm/yarn commands in bash
- Example: `yarn install`, `yarn dev`, `yarn gen:sdk`

### Code Style & Patterns

**Backend (Python/FastAPI):**
- Follow existing router patterns in `backend/api/routers/`
- Use dependency injection via `backend/api/dependencies.py`
- Leverage `BackgroundTasks` for long-running operations
- Implement SSE streaming for progress updates
- Add comprehensive error handling with appropriate HTTP status codes
- Use type hints and Pydantic models
- Follow the config schema pattern from `backend/config_schema.py`

**Frontend (Next.js/TypeScript):**
- Use Server Components where possible (Next.js 15 App Router)
- Follow existing design token system (`text-body-*`, `size-icon-*`)
- Implement loading states with `loading.tsx` pattern
- Use shadcn/ui components from `components/ui/`
- Leverage the app store pattern from `stores/app-store.tsx`
- Maintain type safety with Zod schemas
- Follow SSE streaming pattern from chat route

**Services:**
- Keep service layer modular (see `backend/services/`)
- Use async/await patterns consistently
- Implement proper resource cleanup
- Add comprehensive logging

### Testing Requirements

- **Backend/ColPali:** Test all new API endpoints in WSL using `uv` environment
- **Frontend:** Test UI components in bash terminal using yarn commands
- Validate error handling and edge cases
- Test UI components across different screen sizes
- Verify SSE streaming functionality
- Test Docker builds for all profiles (use WSL for backend/ColPali Docker operations)
- Validate configuration schema updates

### Documentation Requirements

- Add docstrings to all new Python functions/classes
- Include JSDoc comments for TypeScript functions
- Update OpenAPI schema (regenerate with `scripts/generate_openapi.py`)
- Regenerate frontend SDK/Zod schemas (`yarn gen:sdk`, `yarn gen:zod`)
- Update relevant markdown files in `backend/docs/` and root

---

## Progress Tracking Legend

- 🟩 **Done** – Implemented, tested, and documented
- 🟨 **In Progress** – Currently being worked on
- 🟥 **To Do** – Not yet started

**Progress Calculation:**
```
Progress % = (Completed Subtasks / Total Subtasks) × 100
```

---

## Phase 3: Implementation

### Development Environment Setup

**Before starting implementation, ensure:**
- WSL is available for backend/ColPali work
- `uv` is installed in WSL for Python package management
- bash terminal is available for frontend work
- Both terminals can access the project directory

### Implementation Prompt

Once the plan is complete and reviewed, use this prompt to begin implementation:

```
Now implement precisely as planned, in full.

Implementation Requirements:

- Write elegant, minimal, modular code
- Adhere strictly to existing code patterns, conventions, and best practices
- Follow the architecture patterns established in this codebase:
  * Backend: Router → Service → Model pattern
  * Frontend: Page → Component → Store pattern
  * Configuration: Schema-driven runtime config
  * Streaming: SSE for real-time updates
- **CRITICAL:** Use WSL terminal with `uv` for all backend and ColPali service changes
- **CRITICAL:** Use bash terminal for all frontend changes
- Include thorough, clear comments/documentation within the code
- As you implement each step:
  * Update this markdown tracking document with emoji status
  * Update overall progress percentage dynamically
  * Note any deviations from the plan (with justification)
```

---

## Context-Specific Notes

### Key Project Patterns to Follow

1. **Background Jobs with Progress Tracking**
   - See `backend/api/routers/indexing.py` for job management
   - Use `backend/api/progress.py` for SSE streaming
   - Store job state in memory or extend for persistence

2. **Runtime Configuration**
   - Use `backend/config_schema.py` for schema definitions
   - Handle updates via `backend/runtime_config.py`
   - Expose endpoints in `backend/api/routers/config.py`

3. **Service Integration**
   - MinIO: `backend/services/minio.py`
   - Qdrant: `backend/services/qdrant/`
   - ColPali: `backend/services/colpali.py`

4. **Frontend API Integration**
   - Use Zodios client pattern from `frontend/lib/api/`
   - Regenerate types after OpenAPI changes
   - Follow SSE streaming from `frontend/app/api/chat/route.ts`

5. **Docker Considerations**
   - Update `docker-compose.yml` for new services
   - Modify `backend/Dockerfile` or `frontend/Dockerfile` as needed
   - Consider GPU vs CPU profiles for ColPali changes

---

## Post-Implementation Checklist

- [ ] All subtasks marked 🟩
- [ ] Code passes pre-commit hooks (autoflake, isort, black, pyright)
- [ ] OpenAPI spec regenerated and frontend types updated
- [ ] Manual testing completed successfully
- [ ] Documentation updated (README, docs/, inline comments)
- [ ] Environment variable examples updated (`.env.example`, `frontend/.env.example`)
- [ ] Docker builds succeed for all profiles
- [ ] No breaking changes to existing features (or documented if unavoidable)

---

## Notes & Deviations

*(Document any changes from the original plan during implementation)*

---

**End of Plan Template**
