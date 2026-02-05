# SDLC Checklist — Python FastAPI

## Phase 1: Requirements & Planning
- [ ] PRD written with API endpoint specification
- [ ] User stories for each API capability
- [ ] Data model / ERD defined
- [ ] Authentication/authorization requirements
- [ ] Rate limiting and scaling requirements
- [ ] Stakeholder sign-off

## Phase 2: Development & Git
- [ ] Project initialized with pyproject.toml
- [ ] Virtual environment configured (venv/poetry/uv)
- [ ] Ruff + black configured for linting/formatting
- [ ] mypy configured for type checking
- [ ] Project structure: routers, models, schemas, services
- [ ] Pre-commit hooks installed
- [ ] Git branching strategy documented

## Phase 3: CI/CD Pipeline
- [ ] GitHub Actions: lint → type-check → test → build
- [ ] Docker image build and push
- [ ] Dependency vulnerability scanning (pip-audit)
- [ ] SAST scanning (bandit)
- [ ] Database migration CI check (alembic)

## Phase 4: QA Testing
- [ ] Unit tests with pytest (services, utils)
- [ ] Integration tests (API endpoints with TestClient)
- [ ] Database tests with test fixtures
- [ ] Load testing with locust or k6
- [ ] Coverage ≥ 80%

## Phase 5: User Acceptance Testing
- [ ] UAT environment deployed with test database
- [ ] API documentation (Swagger/ReDoc) reviewed
- [ ] All endpoints manually verified
- [ ] Error responses validated
- [ ] Sign-off obtained

## Phase 6: Production Deployment
- [ ] Docker image optimized (multi-stage, slim base)
- [ ] Environment variables configured (secrets manager)
- [ ] Database migrations run
- [ ] Health check endpoint verified
- [ ] Gunicorn/uvicorn production config
- [ ] Deployment runbook documented
- [ ] Rollback: redeploy previous image + rollback migration

## Phase 7: Monitoring & SRE
- [ ] Structured logging (JSON)
- [ ] Request tracing (correlation IDs)
- [ ] Prometheus metrics endpoint (/metrics)
- [ ] Error tracking (Sentry)
- [ ] Database connection pool monitoring
- [ ] Uptime and latency alerts
