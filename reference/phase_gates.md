# Phase Gates — Entry & Exit Criteria

## How Gates Work

Each phase has **entry criteria** (prerequisites) and **exit criteria** (deliverables). The gate validator (`scripts/gate_validator.py`) checks exit criteria automatically. Entry criteria are validated by checking the previous phase's gate.

## Phase 1: Requirements & Planning

**Entry**: Project idea or business need identified
**Exit**:
- [ ] PRD document exists with problem statement, goals, scope
- [ ] User stories written with INVEST criteria
- [ ] Acceptance criteria defined for each story
- [ ] Technical feasibility assessed
- [ ] Stakeholders identified and sign-off recorded
- [ ] Success metrics defined (quantifiable)

## Phase 2: Development & Git

**Entry**: Requirements gate passed
**Exit**:
- [ ] Git repository initialized with branching strategy
- [ ] Pre-commit hooks configured (lint, format, secrets scan)
- [ ] Core features implemented per user stories
- [ ] Code reviewed and approved
- [ ] README with setup instructions

## Phase 3: CI/CD Pipeline

**Entry**: Development gate passed, code in version control
**Exit**:
- [ ] CI pipeline runs on every push (build + test)
- [ ] Linting and formatting enforced in pipeline
- [ ] Security scanning (SAST) configured
- [ ] Branch protection rules active
- [ ] Pipeline tested end-to-end successfully

## Phase 4: QA Testing

**Entry**: CI/CD gate passed, pipeline green
**Exit**:
- [ ] Unit test coverage ≥ 80%
- [ ] Integration tests for critical paths
- [ ] E2E tests for key user journeys
- [ ] Performance/load tests executed
- [ ] All critical/high bugs resolved
- [ ] Test coverage report generated

## Phase 5: User Acceptance Testing

**Entry**: Testing gate passed
**Exit**:
- [ ] UAT plan created from user stories
- [ ] UAT environment provisioned
- [ ] All UAT test cases executed
- [ ] Feedback triaged and blocking issues resolved
- [ ] Stakeholder sign-off obtained

## Phase 6: Production Deployment

**Entry**: UAT gate passed, stakeholder sign-off
**Exit**:
- [ ] Deployment runbook documented
- [ ] Rollback procedure tested
- [ ] Deployment strategy selected and configured
- [ ] Pre-deployment smoke tests pass
- [ ] Post-deployment smoke tests pass
- [ ] Feature flags configured (if applicable)

## Phase 7: Monitoring & SRE

**Entry**: Deployment gate passed, application live
**Exit**:
- [ ] Application metrics being collected
- [ ] Log aggregation configured
- [ ] SLOs defined with error budgets
- [ ] Alerting rules active and tested
- [ ] Dashboards created for key metrics
- [ ] Incident response procedure documented

## Gate Validation

```bash
# Check a specific phase
python scripts/gate_validator.py --phase requirements

# Check all phases
python scripts/gate_validator.py --all

# Output as JSON (for automation)
python scripts/gate_validator.py --phase testing --json
```
