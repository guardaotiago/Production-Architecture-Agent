# Feature Flags Reference

## What Are Feature Flags?

Feature flags (also called feature toggles) are conditional statements in code that control whether a feature is enabled or disabled at runtime, without redeploying. They decouple **deployment** (shipping code to production) from **release** (making the feature available to users).

```python
# Simple feature flag example
if feature_flags.is_enabled("new-checkout-flow", user=current_user):
    return render_new_checkout()
else:
    return render_old_checkout()
```

### Why Use Feature Flags?
- **Safe deployments** — deploy code with new features hidden behind flags
- **Gradual rollouts** — enable for 1% of users, then 10%, then 50%, then 100%
- **Instant rollback** — disable a flag instead of redeploying
- **A/B testing** — show different experiences to different user segments
- **Trunk-based development** — merge incomplete features to main without exposing them

---

## Types of Feature Flags

### 1. Release Flags
**Purpose:** Control the rollout of new features.
**Lifespan:** Short (days to weeks). Remove once feature is fully rolled out.

```json
{
  "name": "new-checkout-flow",
  "type": "release",
  "enabled": true,
  "rollout_percentage": 25,
  "created": "2026-01-15",
  "owner": "checkout-team",
  "cleanup_by": "2026-02-15"
}
```

### 2. Experiment Flags
**Purpose:** A/B testing and experimentation.
**Lifespan:** Short to medium (weeks to months). Remove once experiment concludes.

```json
{
  "name": "pricing-page-variant-b",
  "type": "experiment",
  "variants": ["control", "variant-a", "variant-b"],
  "allocation": {"control": 34, "variant-a": 33, "variant-b": 33},
  "metrics": ["conversion_rate", "revenue_per_user"]
}
```

### 3. Operational Flags (Ops Toggles)
**Purpose:** Control operational behavior in production. Kill switches, circuit breakers, graceful degradation.
**Lifespan:** Long-lived (permanent until the system changes).

```json
{
  "name": "enable-elasticsearch-fallback",
  "type": "ops",
  "enabled": false,
  "description": "Fall back to database search if Elasticsearch is down"
}
```

### 4. Permission Flags
**Purpose:** Control access to features based on user attributes (plan, role, org).
**Lifespan:** Long-lived (tied to business logic).

```json
{
  "name": "advanced-analytics",
  "type": "permission",
  "rules": [
    {"attribute": "plan", "operator": "in", "values": ["pro", "enterprise"]},
    {"attribute": "role", "operator": "eq", "value": "admin"}
  ]
}
```

---

## Implementation Approaches

### 1. Configuration File
Simplest approach. Store flags in a JSON/YAML file that is read at startup.

```json
// flags.json
{
  "flags": {
    "new-checkout-flow": true,
    "dark-mode": false,
    "api-rate-limit": 1000
  }
}
```

**Pros:** Simple, no dependencies, version controlled.
**Cons:** Requires restart or file reload to change flags. No per-user targeting.

### 2. Environment Variables
Good for operational flags that differ between environments.

```bash
FEATURE_NEW_CHECKOUT=true
FEATURE_DARK_MODE=false
```

**Pros:** Simple, works everywhere, easy to set per environment.
**Cons:** Requires restart to change. No granularity (on/off only). Gets unwieldy at scale.

### 3. Database-Backed
Store flags in a database table. Query at runtime.

```sql
CREATE TABLE feature_flags (
    name VARCHAR(255) PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INT DEFAULT 0,
    rules JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Pros:** Dynamic changes without restart. Can build admin UI. Good for small-medium scale.
**Cons:** Database dependency for every flag check (use caching). Must build management UI yourself.

### 4. Feature Flag Service
Use a dedicated service like LaunchDarkly, Unleash, Flagsmith, or Split.

**LaunchDarkly** — SaaS, enterprise-grade, SDKs for every language. Expensive.
**Unleash** — Open source, self-hosted option. Good for teams that want control.
**Flagsmith** — Open source, SaaS option. Good balance of features and simplicity.

**Pros:** Rich targeting rules, audit logs, A/B testing built in, no maintenance.
**Cons:** Cost, external dependency, potential latency.

### Recommendation by Team Size
| Team Size | Recommendation |
|-----------|---------------|
| 1-5 developers | Config file or environment variables |
| 5-20 developers | Database-backed with simple admin UI, or Unleash |
| 20+ developers | LaunchDarkly or Unleash (self-hosted) |

---

## Flag Lifecycle

Every feature flag should follow this lifecycle:

```
CREATE → ENABLE (gradual) → FULL ROLLOUT → CLEANUP (remove flag)
```

### 1. Create
- Add the flag with a clear name, owner, type, and cleanup date
- Document what the flag controls in the flag registry

### 2. Enable (Gradual Rollout)
- Enable for internal users / staff first
- Increase to 5% of real users, monitor
- Increase to 25%, 50%, 100% as confidence grows
- Each stage should have defined metrics to watch

### 3. Full Rollout
- Flag is enabled for 100% of users
- The feature is now fully released

### 4. Cleanup
- **Remove the flag from code** — delete the conditional, keep only the enabled path
- **Remove from flag storage** — delete from config/database/service
- **Remove associated tests** — update tests that check flag behavior
- **This step is critical** — flags that are never cleaned up become technical debt

---

## Cleanup Strategy

Flag debt is real and accumulates quickly. Enforce cleanup discipline:

### Cleanup Rules
1. **Every flag must have an owner** and a `cleanup_by` date when created
2. **Release flags** must be cleaned up within 2 weeks of 100% rollout
3. **Experiment flags** must be cleaned up within 1 week of experiment conclusion
4. **Ops flags** are exempt from cleanup deadlines but must be reviewed quarterly
5. **Permission flags** are permanent but must be documented

### Automated Enforcement
- Run a weekly report of flags past their cleanup date
- Add a linter rule that warns if flag count exceeds a threshold
- Track flag count as a team metric (lower is better)
- Block PR merge if a new flag is added without a `cleanup_by` date

### Cleanup Checklist
- [ ] Remove flag check from code (keep the enabled branch)
- [ ] Remove flag from configuration / flag service
- [ ] Update or remove tests that reference the flag
- [ ] Remove any flag-specific monitoring/alerts
- [ ] Update documentation

---

## Testing with Feature Flags

### Unit Tests
Test both the enabled and disabled paths of every flag.

```python
def test_checkout_with_new_flow_enabled(self):
    with feature_flag_override("new-checkout-flow", True):
        response = self.client.get("/checkout")
        assert "new-checkout" in response.content

def test_checkout_with_new_flow_disabled(self):
    with feature_flag_override("new-checkout-flow", False):
        response = self.client.get("/checkout")
        assert "old-checkout" in response.content
```

### Integration Tests
- Run the full test suite with all flags enabled (future state)
- Run the full test suite with all flags disabled (current state)
- Run with realistic flag combinations for production

### Testing Matrix
For N flags, testing all 2^N combinations is impractical. Instead:
- Test each flag individually (enabled and disabled)
- Test the production configuration
- Test the "all enabled" configuration
- Test known risky combinations

---

## Anti-Patterns

### 1. Flag Explosion
**Problem:** Hundreds of flags with no cleanup, making code unreadable.
**Solution:** Enforce cleanup deadlines. Track flag count. Review quarterly.

### 2. Nested Flags
**Problem:** Flag inside a flag creates combinatorial complexity.
```python
# BAD: nested flags
if is_enabled("feature-a"):
    if is_enabled("feature-b"):
        do_something()  # What does this combination mean?
```
**Solution:** Create a single flag that represents the combined behavior.

### 3. Long-Lived Release Flags
**Problem:** A release flag that has been at 100% for 6 months but was never cleaned up.
**Solution:** Automated alerts when flags pass their cleanup date.

### 4. Using Flags for Configuration
**Problem:** Using feature flags for values that should be configuration (timeouts, URLs, limits).
**Solution:** Use proper configuration management for operational values. Reserve flags for feature visibility.

### 5. No Default Fallback
**Problem:** Code crashes if the flag service is unreachable.
**Solution:** Always define a safe default (usually `false` / disabled) and cache flag values.

```python
# GOOD: safe default
def is_enabled(flag_name: str, default: bool = False) -> bool:
    try:
        return flag_service.evaluate(flag_name)
    except FlagServiceError:
        return default
```

### 6. Flags in Libraries
**Problem:** Shared libraries with feature flags create hidden dependencies.
**Solution:** Keep flags in application code only. Libraries should expose configuration, not flags.
