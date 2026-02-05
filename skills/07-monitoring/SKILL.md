---
name: monitoring-sre
description: Observability setup, alerting, and incident response
version: 1.0.0
phase: 7
commands:
  - /monitor
---

# Phase 7: Monitoring & SRE

## Purpose
Ensure production systems are observable, reliable, and recoverable. Monitoring closes the SDLC feedback loop — production insights drive future requirements and improvements.

## Workflow

### Step 1: Define SLOs
Before configuring monitoring, define what "healthy" means:
- **SLO** (Service Level Objective): target reliability (e.g., 99.9% uptime)
- **SLI** (Service Level Indicator): the metric that measures it (e.g., successful requests / total requests)
- **Error Budget**: how much unreliability you can tolerate (e.g., 0.1% = ~43 min/month downtime)

### Step 2: Set Up the Three Pillars of Observability
See `reference/observability_guide.md`:

**Metrics** (what's happening):
- Request rate, error rate, latency (RED method)
- CPU, memory, disk, network (USE method)
- Business metrics (signups, conversions, revenue)

**Logs** (why it's happening):
- Structured JSON format
- Correlation IDs for request tracing
- Log levels: ERROR, WARN, INFO, DEBUG

**Traces** (where it's happening):
- Distributed tracing across services
- Span context propagation
- Trace sampling for high-volume systems

### Step 3: Generate Alert Rules
```bash
python skills/07-monitoring/scripts/alert_generator.py --slo 99.9 --service "my-api" --output alerts/
```
Generates alert rules based on SLOs with appropriate severity levels and runbook links.

### Step 4: Create Dashboards
Essential dashboards:
- **Service overview**: request rate, error rate, latency (p50/p95/p99)
- **Infrastructure**: CPU, memory, disk, network
- **Business KPIs**: core business metrics
- **Deployment tracker**: recent deploys correlated with metrics

### Step 5: Set Up Incident Response
See `reference/incident_response.md` for the full playbook.

```bash
python skills/07-monitoring/scripts/incident_report.py --incident "API latency spike" --severity P1 --output docs/incidents/
```

Incident severity levels:
- **P0 (Critical)**: Complete outage, all users affected. Response: immediate.
- **P1 (High)**: Major feature broken, many users affected. Response: < 15 min.
- **P2 (Medium)**: Degraded service, some users affected. Response: < 1 hour.
- **P3 (Low)**: Minor issue, few users affected. Response: next business day.

### Step 6: Gate Check
```bash
python scripts/gate_validator.py --phase monitoring
```

## Phase Exit Criteria
- [ ] Monitoring configured (metrics, logs, traces)
- [ ] Alerting rules defined and tested
- [ ] SLOs documented with error budgets
- [ ] Incident response plan exists
- [ ] Dashboards created

## Reference Docs
- `reference/observability_guide.md` — Metrics, logs, and traces setup
- `reference/incident_response.md` — Incident management playbook
