# Deployment Strategies Reference

## Overview

Choosing the right deployment strategy depends on your risk tolerance, infrastructure capabilities, and the nature of the change. This guide covers the four primary strategies and when to use each.

---

## 1. Canary Deployment

### How It Works
Deploy the new version to a small subset of infrastructure and gradually shift traffic from the old version to the new version. Monitor at each stage before increasing the traffic percentage.

### Traffic Ramp-Up Schedule

| Stage | Traffic % | Duration | Action if Unhealthy |
|-------|-----------|----------|---------------------|
| 1 | 5% | 5 min | Rollback immediately |
| 2 | 25% | 10 min | Rollback immediately |
| 3 | 50% | 10 min | Rollback immediately |
| 4 | 100% | 30 min bake | Rollback if issues appear |

### Implementation Approaches
- **Load balancer weighted routing** — AWS ALB weighted target groups, Nginx upstream weights
- **Service mesh** — Istio VirtualService traffic splitting, Linkerd traffic split
- **Kubernetes** — Argo Rollouts canary strategy, Flagger

### Pros
- Low risk: only a fraction of users see the new version initially
- Easy rollback: shift traffic back to stable version
- Real production validation before full rollout

### Cons
- Requires traffic splitting infrastructure
- Longer deployment time
- Both versions run simultaneously (must be compatible)

### Best For
- High-traffic services where failures are costly
- Risk-averse teams or regulated environments
- Changes that are difficult to test in staging

---

## 2. Blue-Green Deployment

### How It Works
Maintain two identical production environments: **Blue** (current live) and **Green** (idle). Deploy the new version to the idle environment, verify it, then switch all traffic at once via DNS or load balancer.

### Switching Mechanisms

| Method | Switch Time | Complexity |
|--------|-------------|------------|
| DNS CNAME | 30-300s (TTL) | Low |
| Load balancer target swap | 1-5s | Medium |
| Reverse proxy config | 1-5s | Medium |
| Kubernetes service selector | 1-5s | Low |

### Implementation
1. Identify active environment (e.g., Blue is live)
2. Deploy new version to Green
3. Run smoke tests against Green directly
4. Switch traffic from Blue to Green
5. Keep Blue running as rollback target
6. After bake period, decommission Blue (or keep as next deploy target)

### Pros
- Instant rollback: switch back to the old environment
- Full environment tested before any user traffic
- Simple mental model

### Cons
- Requires double infrastructure (cost)
- Database schema must be compatible with both versions during switchover
- Not ideal for stateful applications without shared storage

### Best For
- Zero-downtime requirements
- Services where you want full pre-validation
- Teams that can afford double infrastructure

---

## 3. Rolling Update

### How It Works
Gradually replace instances of the old version with the new version, one or a few at a time. This is the default strategy in Kubernetes deployments.

### Kubernetes Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # max extra pods during update
      maxUnavailable: 0   # no downtime
  template:
    spec:
      containers:
      - name: my-service
        image: my-service:v2.0.0
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
```

### Key Parameters
- **maxSurge** — how many extra pods can exist during update (set to 1 or 25%)
- **maxUnavailable** — how many pods can be unavailable (set to 0 for zero downtime)
- **readinessProbe** — must pass before pod receives traffic
- **livenessProbe** — restarts pod if it fails

### Pros
- No additional infrastructure needed
- Native to Kubernetes
- Gradual rollout reduces blast radius

### Cons
- Both versions serve traffic simultaneously during rollout
- Rollback requires redeploying the old version (slower than canary/blue-green)
- Hard to control exact traffic split

### Best For
- Stateless services on Kubernetes
- Teams wanting simple, infrastructure-native deployments
- Changes with low risk or well-tested in staging

---

## 4. Recreate (Stop-Start)

### How It Works
Stop all instances of the old version, then start instances of the new version. Simple but causes downtime.

### Process
1. Scale down all old instances to 0
2. Deploy new version
3. Scale up new instances
4. Verify health

### Pros
- Simplest strategy
- No version compatibility concerns
- Clean state

### Cons
- **Causes downtime** — unacceptable for most production services
- No gradual validation
- Slow rollback (must redeploy old version)

### Best For
- Development and staging environments only
- Services with scheduled maintenance windows
- Stateful applications that cannot run two versions simultaneously

---

## Strategy Comparison

| Criteria | Canary | Blue-Green | Rolling | Recreate |
|----------|--------|------------|---------|----------|
| Zero downtime | Yes | Yes | Yes | **No** |
| Rollback speed | Fast | Instant | Moderate | Slow |
| Infrastructure cost | Low-Med | High (2x) | None | None |
| Traffic control | Fine-grained | All-or-nothing | Coarse | N/A |
| Complexity | Medium | Medium | Low | Very Low |
| Risk level | Low | Low | Medium | High |
| Best environment | Production | Production | Production | Dev/Staging |

---

## Database Migration Strategies During Deployment

Database changes are the hardest part of deployment because they are difficult to roll back. Follow these principles:

### Expand-Contract Pattern
1. **Expand** — Add new columns/tables without removing old ones. Deploy code that writes to both old and new.
2. **Migrate** — Backfill data from old structure to new.
3. **Contract** — Remove old columns/tables once all code uses the new structure (in a future deployment).

### Rules
- **Never drop columns/tables in the same deployment that removes code using them.** Separate by at least one deployment cycle.
- **Always make migrations backward-compatible.** The old version of the code must still work after the migration runs.
- **Test migrations on a production-size dataset** in staging before deploying.
- **Have a rollback migration ready** but understand that data loss may occur if new data was written to new columns.

### Migration Sequence
```
Deploy v1 code (reads column A)
  → Run migration: ADD column B
  → Deploy v2 code (reads A, writes A + B)
  → Run migration: backfill B from A
  → Deploy v3 code (reads B, writes B)
  → Run migration: DROP column A
```

---

## Deployment Windows and Communication

### Choosing a Window
- **Low-traffic periods** — reduces blast radius if something goes wrong
- **Business hours** — ensures full team is available for support
- **Avoid Fridays** — nobody wants to debug over the weekend
- **Coordinate across teams** — avoid deploying multiple services simultaneously

### Communication Checklist
1. Announce deployment window 24 hours in advance (for major changes)
2. Post in team channel when deployment starts
3. Post status updates at each stage (canary 5%, 25%, 50%, 100%)
4. Announce completion or rollback
5. Send post-deployment summary (what changed, any issues)

### Deployment Freeze Periods
Define periods when deployments are not allowed:
- Major sales events (Black Friday, product launches)
- Company all-hands or off-sites
- Holiday weekends
- During active incidents
