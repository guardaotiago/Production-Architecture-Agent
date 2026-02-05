# SDLC Orchestrator

A Claude Code skill repository that manages software projects from concept to production, following the 7-phase SDLC workflow from ByteByteGo's "How Big Tech Ships Code to Production."

## Quick Start

```bash
# 1. Clone or copy into your project
cd your-project
cp -r /path/to/sdlc-orchestrator/.claude/ .

# 2. Initialize SDLC tracking
python /path/to/sdlc-orchestrator/scripts/init_sdlc.py --project-name "My Project"

# 3. Start from any phase
# In Claude Code, use slash commands:
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

| Command | Description |
|---------|-------------|
| `/gate [phase]` | Validate phase exit criteria |
| `/health` | Project health dashboard |
| `/template [stack]` | Initialize from template |

## Inspired By

- [ByteByteGo - How Big Tech Ships Code to Production](https://www.youtube.com/watch?v=example)
- [Awesome Claude Skills](https://github.com/anthropics/awesome-claude-skills) patterns

## License

MIT
