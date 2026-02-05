# Integration Catalog

Available tool integrations organized by SDLC phase. The orchestrator doesn't require any specific tool — these are recommendations that work well with each phase.

## Phase 1: Requirements & Planning

| Tool | Purpose | Integration |
|------|---------|-------------|
| Notion | PRD hosting, collaboration | MCP API tools |
| Linear / Jira | Issue tracking, user stories | API / CLI |
| Figma | UI/UX wireframes | Share links in PRD |
| Miro | Collaborative whiteboarding | Share links |

## Phase 2: Development & Git

| Tool | Purpose | Integration |
|------|---------|-------------|
| GitHub / GitLab | Version control, PRs | Git CLI, `gh` CLI |
| pre-commit | Git hooks framework | `.pre-commit-config.yaml` |
| EditorConfig | Consistent editor settings | `.editorconfig` |
| Conventional Commits | Commit message standard | commitlint hook |

## Phase 3: CI/CD Pipeline

| Tool | Purpose | Integration |
|------|---------|-------------|
| GitHub Actions | CI/CD pipelines | `.github/workflows/` |
| GitLab CI | CI/CD pipelines | `.gitlab-ci.yml` |
| Docker | Containerization | `Dockerfile` |
| Trivy | Container security scanning | CI step |
| SonarQube | Code quality analysis | CI step |

## Phase 4: QA Testing

| Tool | Purpose | Integration |
|------|---------|-------------|
| pytest | Python testing | `pyproject.toml` |
| Vitest | JavaScript/TypeScript testing | `vite.config.ts` |
| Playwright | E2E browser testing | `playwright.config.ts` |
| k6 | Load testing | `k6` scripts |
| Locust | Python load testing | `locustfile.py` |

## Phase 5: User Acceptance Testing

| Tool | Purpose | Integration |
|------|---------|-------------|
| Vercel Preview | Preview deployments | Automatic on PR |
| Netlify Deploy Preview | Preview deployments | Automatic on PR |
| TestRail | UAT test management | Manual |
| Google Forms | Feedback collection | Share link |

## Phase 6: Production Deployment

| Tool | Purpose | Integration |
|------|---------|-------------|
| Vercel | Frontend hosting | `vercel.json` |
| AWS (ECS/EKS) | Container orchestration | Terraform / CDK |
| Fly.io | App hosting | `fly.toml` |
| LaunchDarkly | Feature flags | SDK integration |
| Unleash | Feature flags (OSS) | SDK integration |

## Phase 7: Monitoring & SRE

| Tool | Purpose | Integration |
|------|---------|-------------|
| Prometheus + Grafana | Metrics & dashboards | `/metrics` endpoint |
| Datadog | Full observability | Agent + SDK |
| Sentry | Error tracking | SDK integration |
| PagerDuty | Incident management | Alert routing |
| Better Uptime | Uptime monitoring | HTTP checks |
| OpenTelemetry | Vendor-neutral observability | SDK integration |

## Cross-Phase Tools

| Tool | Purpose | Phases |
|------|---------|--------|
| Claude Code | AI-assisted development | All |
| GitHub CLI (`gh`) | GitHub operations | 2, 3, 6 |
| Docker | Containerization | 3, 4, 5, 6 |
| Terraform | Infrastructure as Code | 3, 6, 7 |
