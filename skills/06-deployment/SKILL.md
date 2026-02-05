---
name: production-deployment
description: Safe production deployment with rollback strategies
version: 1.0.0
phase: 6
commands:
  - /deploy [strategy]
---

# Phase 6: Production Deployment

## Purpose
Ship code to production safely and reliably. The goal is zero-downtime deployments with instant rollback capability. Deployment should be boring — a non-event.

## Workflow

### Step 1: Generate Deployment Runbook
```bash
python skills/06-deployment/scripts/deployment_plan.py --strategy canary|blue-green|rolling --output docs/deployment-runbook.md
```
Creates a step-by-step runbook with pre-checks, deployment steps, verification, and rollback procedures.

### Step 2: Choose Deployment Strategy
See `reference/deployment_strategies.md` for details:

| Strategy | Best For | Rollback Speed | Risk |
|----------|----------|---------------|------|
| **Canary** | High-traffic, risk-averse | Fast (route traffic) | Low |
| **Blue-Green** | Zero-downtime required | Instant (DNS/LB switch) | Low |
| **Rolling** | Stateless services, k8s | Moderate (replace back) | Medium |
| **Recreate** | Dev/staging only | Slow (redeploy old) | High |

### Step 3: Configure Feature Flags (optional)
See `reference/feature_flags.md`. Decouple deployment from release:
- Deploy code with feature behind flag
- Enable flag for internal users first
- Gradually roll out to wider audience
- Kill switch for instant disable

### Step 4: Pre-Deployment Checklist
- [ ] All gates passed (requirements → UAT)
- [ ] Deployment runbook reviewed
- [ ] Rollback procedure tested
- [ ] Database migrations tested (if applicable)
- [ ] Team notified of deployment window
- [ ] Monitoring dashboards open

### Step 5: Execute Deployment
Follow the runbook. Key steps:
1. Run pre-deployment smoke tests
2. Create deployment tag/release
3. Deploy to production (per strategy)
4. Run post-deployment smoke tests
5. Monitor metrics for anomalies (15-30 min)

### Step 6: Post-Deployment Verification
```bash
python skills/06-deployment/scripts/smoke_test.py --url https://app.example.com --config smoke-tests.json
```

### Step 7: Gate Check
```bash
python scripts/gate_validator.py --phase deployment
```

## Phase Exit Criteria
- [ ] Deployment runbook documented
- [ ] Rollback procedure tested
- [ ] Deployment strategy configured
- [ ] Smoke tests pass pre and post deployment
- [ ] Feature flags configured (if applicable)

## Reference Docs
- `reference/deployment_strategies.md` — Canary, blue-green, rolling strategies
- `reference/feature_flags.md` — Feature flag implementation guide
- `reference/rollback_procedures.md` — Rollback playbooks
