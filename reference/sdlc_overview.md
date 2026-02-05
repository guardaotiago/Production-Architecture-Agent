# Software Development Life Cycle Overview

## The 7 Phases

Based on "How Big Tech Ships Code to Production" (ByteByteGo).

### Phase 1: Requirements & Planning
The product owner defines **what** to build and **why**. Outputs: PRD, user stories with acceptance criteria, success metrics. This phase prevents the #1 cause of project failure: building the wrong thing.

### Phase 2: Development & Git
Developers write code following agreed conventions. Key practices:
- Feature branches off main
- Conventional commits for automated changelogs
- Small, reviewable PRs (< 400 lines)
- Code reviews before merge

### Phase 3: CI/CD Pipeline
Automated pipeline triggers on every push:
1. **Build** — compile/bundle the application
2. **Unit tests** — fast feedback on logic correctness
3. **Lint & format** — enforce code style
4. **Security scan** — SAST for known vulnerabilities
5. **Artifact publish** — Docker image, package, or binary

### Phase 4: QA Testing
Dedicated QA in separate environments:
- **Regression testing** — verify nothing broke
- **Integration testing** — systems work together
- **Performance testing** — load and stress tests
- **Coverage analysis** — identify untested paths

### Phase 5: User Acceptance Testing
Final vetting by stakeholders before go-live:
- UAT environment mirrors production
- Test cases derived from user stories
- Stakeholder sign-off is the gate

### Phase 6: Production Deployment
Ship to production safely:
- **Feature flags** — decouple deploy from release
- **Canary deployment** — route 1-5% traffic first
- **Blue-green** — instant rollback via traffic switch
- **Rolling update** — gradual instance replacement
- Smoke tests post-deploy

### Phase 7: Monitoring & SRE
Observe and respond:
- **Metrics** — Prometheus, Datadog, CloudWatch
- **Logs** — structured, centralized, searchable
- **Traces** — distributed tracing for request flows
- **Alerts** — SLO-based, actionable, not noisy
- **Incident response** — defined process, blameless postmortems

## Phase Flow

```
Requirements → Development → CI/CD → Testing → UAT → Deployment → Monitoring
     ↑                                                                  |
     └─────────────────── continuous feedback ──────────────────────────┘
```

Each phase has **entry criteria** (what must be true to start) and **exit criteria** (what must be true to advance). These "gates" prevent quality debt from compounding downstream.

## Why Gates Matter

Bugs found in requirements cost 1x to fix. In development: 5x. In testing: 15x. In production: 100x. Gates enforce "shift left" — catching issues as early as possible.
