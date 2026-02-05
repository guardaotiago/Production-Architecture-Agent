# SDLC Orchestrator

A Claude Code skill repository that manages software projects from concept to production, following the 7-phase SDLC workflow from ByteByteGo's "How Big Tech Ships Code to Production."

## Quick Start

### Option A: Full guided walkthrough (recommended)

```bash
# One command walks you through all 7 phases interactively
python /path/to/Production-Architecture-Agent/scripts/orchestrate.py \
  --project-dir ~/my-project
```

The orchestrator will:
- Ask you questions at each phase
- Run scripts to generate artifacts (PRD, CI config, test plans, runbooks, alerts)
- Validate gate criteria before advancing
- Save progress — quit anytime with Ctrl+C, resume later

### Option B: Phase-by-phase (manual)

```bash
# 1. Initialize SDLC tracking
python /path/to/Production-Architecture-Agent/scripts/init_sdlc.py --project-name "My Project"

# 2. Work through phases individually:
/plan MyProject        # Phase 1: Requirements
/develop               # Phase 2: Development
/cicd github           # Phase 3: CI/CD
/test all              # Phase 4: Testing
/uat                   # Phase 5: User Acceptance
/deploy canary         # Phase 6: Deployment
/monitor               # Phase 7: Monitoring
```

## The 7 Phases

| Phase | Focus | Key Outputs |
|-------|-------|-------------|
| 1. Requirements | What to build & why | PRD, user stories, acceptance criteria |
| 2. Development | Code & version control | Working code, clean git history |
| 3. CI/CD | Automated build & checks | Pipeline config, quality gates |
| 4. Testing | QA & regression | Test plans, coverage reports |
| 5. UAT | Stakeholder validation | Sign-off documents |
| 6. Deployment | Ship to production | Deployment runbook, rollback plan |
| 7. Monitoring | Observe & respond | Dashboards, alerts, runbooks |

## Architecture

### Progressive Disclosure

Only the content you need is loaded into context:

- **CLAUDE.md** (~1.5KB): Always loaded. Commands and overview.
- **Phase SKILL.md** (~3-5KB): Loaded when a phase command is invoked.
- **Reference docs**: Loaded on explicit request for deep guidance.
- **Scripts**: Executed externally — zero context tokens.

### Gate System

Each phase has entry/exit criteria. Gates must pass before advancing:

```bash
python scripts/gate_validator.py --phase requirements
# ✓ PRD document exists
# ✓ User stories defined
# ✓ Acceptance criteria present
# ✗ Technical feasibility not assessed
# Result: BLOCKED (3/4 criteria met)
```

### Project Templates

Start with battle-tested scaffolding:

```bash
python scripts/init_sdlc.py --template react-vite    # React + TypeScript + Vite
python scripts/init_sdlc.py --template fastapi        # Python FastAPI
python scripts/init_sdlc.py --template nextjs          # Next.js + TypeScript
```

## File Structure

```
sdlc-orchestrator/
├── CLAUDE.md              # Master orchestrator
├── skills/
│   ├── 01-requirements/   # PRD, user stories, planning
│   ├── 02-development/    # Git workflow, coding standards
│   ├── 03-cicd/           # Pipeline setup, Docker, GHA
│   ├── 04-testing/        # Test strategy, coverage analysis
│   ├── 05-uat/            # UAT planning, stakeholder sign-off
│   ├── 06-deployment/     # Deploy strategies, feature flags
│   └── 07-monitoring/     # Observability, incident response
├── templates/             # Project starter templates
├── scripts/               # Global orchestrator scripts
├── reference/             # Cross-phase documentation
└── evaluations/           # Self-testing scenarios
```

## Key Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/plan [name]` | 1 | Start requirements & planning |
| `/develop` | 2 | Initialize dev workflow & git |
| `/cicd [platform]` | 3 | Set up CI/CD (github\|gitlab\|jenkins) |
| `/test [type]` | 4 | Generate tests (unit\|integration\|e2e\|all) |
| `/uat` | 5 | Prepare UAT plan & coordinate sign-off |
| `/deploy [strategy]` | 6 | Deploy (canary\|blue-green\|rolling) |
| `/monitor` | 7 | Set up monitoring, alerts & SRE practices |
| `/gate [phase]` | - | Check phase exit criteria before advancing |
| `/health` | - | Project health dashboard across all phases |
| `/template [stack]` | - | Init from template (react-vite\|fastapi\|nextjs) |

## How to Use This Agent: End-to-End Product Deployment

### Setup (one time)

```bash
# Navigate to your project (or create a new one)
cd ~/my-new-project

# Initialize SDLC tracking (optionally with a template)
python /path/to/Production-Architecture-Agent/scripts/init_sdlc.py \
  --project-name "My Product" --template react-vite
```

This creates `.sdlc/state.json` to track your progress and phase checklists in `.sdlc/phases/`.

---

### Phase 1: Requirements (`/plan`)

Define **what** you're building and **why**. This phase prevents the #1 cause of project failure: building the wrong thing.

```bash
# Interactively gather requirements
python skills/01-requirements/scripts/gather_requirements.py --project "My Product"

# Write your PRD using the template
cat skills/01-requirements/reference/prd_template.md  # Copy and fill in

# Validate PRD completeness
python skills/01-requirements/scripts/validate_prd.py --file docs/prd.md

# Check the gate before moving on
python scripts/gate_validator.py --phase requirements
```

**Gate criteria:** PRD exists, user stories defined, acceptance criteria present, technical feasibility assessed, stakeholder sign-off recorded.

---

### Phase 2: Development (`/develop`)

Set up your dev environment and start coding.

```bash
# Scaffold project structure (node, python, or go)
bash skills/02-development/scripts/init_project.sh --name "my-product" --type node

# Install git hooks (lint, format, secrets scan, commit message validation)
bash skills/02-development/scripts/setup_git_hooks.sh

# Code your features using conventional commits
# Reference: skills/02-development/reference/commit_conventions.md
# Reference: skills/02-development/reference/git_workflow.md

# Check the gate
python scripts/gate_validator.py --phase development
```

**Gate criteria:** Git repo initialized, branching strategy documented, pre-commit hooks configured, README exists, code reviewed.

---

### Phase 3: CI/CD (`/cicd`)

Automate your build-test-deploy pipeline.

```bash
# Generate a CI pipeline config
python skills/03-cicd/scripts/generate_pipeline.py --platform github --type node

# Copy Docker templates if needed
cp skills/03-cicd/assets/docker/Dockerfile.node ./Dockerfile
cp skills/03-cicd/assets/docker/docker-compose.yml ./docker-compose.yml

# Check the gate
python scripts/gate_validator.py --phase cicd
```

**Gate criteria:** CI pipeline runs on every push, build and test steps configured, linting enforced, security scanning active, pipeline verified end-to-end.

---

### Phase 4: Testing (`/test`)

Build confidence through systematic testing.

```bash
# Generate test plan from your PRD
python skills/04-testing/scripts/test_planner.py --prd docs/prd.md --output docs/test-plan.md

# Write and run tests (unit, integration, E2E)
# Reference: skills/04-testing/reference/testing_pyramid.md

# Analyze coverage gaps
python skills/04-testing/scripts/coverage_analyzer.py --report coverage/lcov.info --threshold 80

# Check the gate
python scripts/gate_validator.py --phase testing
```

**Gate criteria:** Unit coverage >= 80%, integration tests for critical paths, E2E tests for key journeys, performance tests executed, all critical bugs resolved.

---

### Phase 5: UAT (`/uat`)

Get stakeholder validation before go-live.

```bash
# Generate UAT plan from user stories
python skills/05-uat/scripts/generate_uat_plan.py --prd docs/prd.md --output docs/uat-plan.md

# Execute with stakeholders, collect and triage feedback
# Reference: skills/05-uat/reference/uat_best_practices.md

# Check the gate
python scripts/gate_validator.py --phase uat
```

**Gate criteria:** UAT plan created, UAT environment provisioned, all test cases executed, blockers resolved, stakeholder sign-off obtained.

---

### Phase 6: Deployment (`/deploy`)

Ship to production safely.

```bash
# Generate deployment runbook for your chosen strategy
python skills/06-deployment/scripts/deployment_plan.py \
  --strategy canary --service-name "my-product" --env production

# After deploying, run smoke tests
python skills/06-deployment/scripts/smoke_test.py \
  --url https://my-product.com --config smoke-tests.json

# Reference: skills/06-deployment/reference/deployment_strategies.md
# Reference: skills/06-deployment/reference/feature_flags.md
# Reference: skills/06-deployment/reference/rollback_procedures.md

# Check the gate
python scripts/gate_validator.py --phase deployment
```

**Gate criteria:** Deployment runbook documented, rollback procedure tested, strategy configured, smoke tests pass pre and post deployment.

---

### Phase 7: Monitoring (`/monitor`)

Observe, alert, and respond. This phase closes the feedback loop.

```bash
# Generate alert rules from your SLOs
python skills/07-monitoring/scripts/alert_generator.py \
  --slo 99.9 --service "my-product" --output alerts/

# If an incident occurs, generate a postmortem template
python skills/07-monitoring/scripts/incident_report.py \
  --incident "API latency spike" --severity P1 --output docs/incidents/

# Reference: skills/07-monitoring/reference/observability_guide.md
# Reference: skills/07-monitoring/reference/incident_response.md

# Check the gate
python scripts/gate_validator.py --phase monitoring
```

**Gate criteria:** Monitoring configured, alerting rules defined, SLOs documented, incident response plan exists, dashboards created.

---

### Anytime: Check Project Health

```bash
python scripts/project_health.py
```

Displays a dashboard with all phases, progress percentages, gate status, and actionable recommendations.

```bash
# Validate all gates at once
python scripts/gate_validator.py --all
```

---

### Key Principles

1. **Never skip gates** -- Run `gate_validator.py --phase <name>` before advancing. Bugs found in requirements cost 1x to fix; in production, 100x.
2. **Scripts are black boxes** -- Run `--help` first. Only read source code if you need to customize.
3. **Reference docs on demand** -- Only load `skills/0X-phase/reference/` docs when you need deep guidance.
4. **Feedback loop** -- Phase 7 monitoring insights feed back into Phase 1 requirements. The cycle never truly ends.
5. **Progressive disclosure** -- CLAUDE.md is always loaded (~2KB). Phase SKILL.md loads only when invoked (~3KB). Total active context stays under 10KB.

## Inspired By

- [ByteByteGo - How Big Tech Ships Code to Production](https://www.youtube.com/watch?v=example)
- [Awesome Claude Skills](https://github.com/anthropics/awesome-claude-skills) patterns

## License

MIT
