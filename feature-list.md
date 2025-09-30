# Production Feature List

This checklist captures key tasks to take this template (FastAPI + Next.js + Qdrant + MinIO + ColPali service) to production. It references files/paths in this repo to keep implementation concrete.

- __Security & Access Control__

  - [ ] Add OIDC/JWT auth and protect routes (all except `GET /health`).
    - Backend: add security scheme and route guards in `backend/api/app.py` and `backend/api/routers/*`.
    - Frontend: session handling/protected pages.
  - [ ] Tighten CORS to explicit origins only via `ALLOWED_ORIGINS` in `backend/config.py`.
  - [ ] Make MinIO bucket private; serve images via presigned URLs; enable SSE (SSE-S3/KMS).
    - Update `backend/services/minio.py`; set `MINIO_PUBLIC_READ=False` in `.env`.
  - [ ] Secrets management (move secrets from `.env` to Secret Manager or Kubernetes Secrets/SealedSecrets).
  - [ ] Reverse proxy + TLS termination (Traefik/Nginx/Caddy), HSTS, HTTP→HTTPS.
  - [ ] Upload hardening: max file size, MIME/type checks, and optional malware scan.
  - [ ] Rate limiting (per-IP and per-identity) via middleware (e.g., `slowapi`/`starlette-limiter`).
- __Reliability & Performance__

  - [ ] Offload indexing to background jobs (Celery/RQ/Arq) + job status endpoints.
  - [ ] Add client timeouts, retries with backoff, and circuit breakers for calls to OpenAI, ColPali, MinIO, Qdrant.
    - Touch `backend/services/*.py` and shared HTTP client config.
  - [ ] Production server: `gunicorn` + `uvicorn.workers.UvicornWorker`; tune workers/threads/timeouts/keepalive.
    - Update `backend/Dockerfile` and container entrypoint.
  - [ ] Health/readiness/liveness endpoints and container healthchecks.
    - Add detailed `/health` in `backend/api/routers/meta.py`; augment `docker-compose.yml` healthchecks.
  - [ ] Resource limits/requests in containers (CPU/memory) and autoscaling strategy (if k8s).
  - [ ] Optional caching (Redis) for search/chat responses.
- __Observability__

  - [ ] Structured JSON logging with request IDs and redaction of sensitive fields.
    - Centralize logging in `backend/` and propagate correlation IDs.
  - [ ] Metrics: expose Prometheus `/metrics` (HTTP latency, codes, indexing/search counters).
    - Add `prometheus-fastapi-instrumentator` to `backend/api/app.py`.
  - [ ] Tracing: OpenTelemetry for FastAPI and HTTP clients; export to Jaeger/Tempo/Cloud Trace.
  - [ ] Error tracking: Sentry SDK for backend and frontend.
- __Data Durability & Ops__

  - [ ] Qdrant: snapshot/backup automation; restore runbook; resource sizing; optional replication/HA.
  - [ ] MinIO: bucket versioning, lifecycle policies, replication (multi-AZ), quotas/alerts.
  - [ ] Schema/versioning: scripts for collection creation/migration; embed schema version in payload.
  - [ ] Reindex/backfill jobs and operational runbooks (rotate keys, rollbacks, DR drills).
- __Frontend (Next.js)__

  - [ ] Production build with `output: 'standalone'` and pinned Node version.
    - Configure in `frontend/next.config.ts`.
  - [ ] Security headers: CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (at proxy).
    - Add `headers()` in `frontend/next.config.ts`.
  - [ ] Error boundary + Sentry browser SDK; redact PII in logs.
  - [ ] Configure image domains and use a CDN for static assets.
  - [ ] Validate env vars (public vs server-only) at build time.
- __CI/CD & Governance__

  - [ ] CI: lint, type-check, tests; build Docker images; SBOM + vulnerability scan (Trivy/Grype); push to registry.
    - Add `.github/workflows/ci.yml`.
  - [ ] CD: environment promotion (dev→staging→prod), config per environment, blue/green or canary.
  - [ ] Dependency hygiene: Renovate/Dependabot; pin base images; reproducible builds.
  - [ ] Supply chain: image signing (cosign), provenance (SLSA) as needed.
- __Infrastructure__

  - [ ] Reverse proxy config (Traefik/Nginx/Caddy) with Let’s Encrypt certs and security headers.
  - [ ] Container registry and image retention policy.
  - [ ] IaC for cloud resources (Terraform) and/or Helm/Kubernetes manifests (if targeting k8s).
  - [ ] Autoscaling/HA strategy (HPA for k8s; or scale sets/ASG for VMs).
- __LLM Safety & Cost Controls__

  - [ ] Usage caps and concurrency limits for OpenAI calls; per-tenant quotas if multi-tenant.
  - [ ] Moderation filters (provider or local) and prompt hygiene.
  - [ ] Response caching and batch processing where possible.
  - [ ] Logging policy: redact prompts/outputs or hash sensitive values.
- __Compliance & Audit__

  - [ ] Audit logs for admin/indexing/maintenance actions; immutable storage/retention.
  - [ ] Data lifecycle: retention, export, and delete workflows (e.g., GDPR/DSAR support).

## Suggested environment additions in `.env.example`

Add the following toggles/placeholders to support the features above:

- Auth: `AUTH_PROVIDER`, `AUTH_ISSUER_URL`, `AUTH_AUDIENCE`, `AUTH_JWKS_URL`.
- Rate limiting: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`.
- MinIO: `MINIO_PUBLIC_READ=false`, `MINIO_USE_PRESIGNED_URLS=true`, `MINIO_SSE=auto|kms`, `MINIO_KMS_KEY_ID`.
- Observability: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `SENTRY_DSN`.
- Server: `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT`, `MAX_UPLOAD_MB`.
- CORS: `ALLOWED_ORIGINS` (comma-separated, no wildcards in prod).

## Minimum Viable Hardening (suggested first PR)

- [ ] Lock down MinIO (private bucket + presigned URLs); remove public-read policy.
- [ ] Tighten CORS to explicit origins.
- [ ] Switch backend to `gunicorn` + `uvicorn` workers; set sane timeouts.
- [ ] Add container healthchecks and `/health` dependency checks.
- [ ] Structured JSON logging and request IDs.
- [ ] Basic rate limiting.
- [ ] Next.js security headers and image domain restrictions.

## Nice-to-have (next phase)

- [ ] Background worker for indexing with a queue.
- [ ] Prometheus metrics + Grafana dashboards; OpenTelemetry traces.
- [ ] Sentry across backend/frontend.
- [ ] CI with Trivy image scan and SBOM; push to registry; CD to staging/prod.
- [ ] Qdrant snapshot automation and restore runbook.
