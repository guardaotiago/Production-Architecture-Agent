# Rollback Procedures Reference

## Overview

A rollback is the process of reverting a production deployment to a previously known-good state. Every deployment must have a tested rollback plan **before** it is executed. The goal is to restore service as fast as possible, then investigate root cause afterward.

**Golden rule:** When in doubt, roll back. You can always redeploy later. Trying to fix forward under pressure causes more incidents than it resolves.

---

## Rollback Triggers

Roll back immediately if **any** of the following are observed after deployment:

### Automated Triggers (Alert-Based)
| Signal | Threshold | Action |
|--------|-----------|--------|
| Error rate (5xx) | > 1% of requests (or > 2x baseline) | Roll back |
| Latency p99 | > 2x baseline for 5+ minutes | Roll back |
| Availability | < 99.9% (or below SLO) | Roll back |
| Pod crash loops | Any pod in CrashLoopBackOff | Roll back |
| Health check failures | > 0 failing health checks | Roll back |
| Memory/CPU | > 90% utilization (sustained) | Investigate, likely roll back |

### Manual Triggers (Human-Observed)
- User-reported errors or broken functionality
- Key business metrics drop (conversion rate, sign-ups, revenue)
- Data inconsistency or corruption detected
- Security vulnerability discovered in deployed code
- Deployment lead or on-call engineer calls for rollback

### When NOT to Roll Back
- Cosmetic issues that do not affect functionality (typo in UI, wrong icon)
- Expected behavior changes that users are reporting as bugs (communicate instead)
- Metrics fluctuation within normal variance

---

## Rollback by Strategy

### Canary Rollback

**Time to recover:** < 1 minute (traffic shift)

**Steps:**
1. Shift 100% of traffic back to the stable (old) version
   - Load balancer: update target group weights to 100/0
   - Service mesh: update VirtualService routing to 100% stable
   - Argo Rollouts: `kubectl argo rollouts abort <rollout-name>`
2. Verify traffic is no longer reaching canary instances
3. Run smoke tests against production URL to confirm stability
4. Keep canary instances running for investigation (do not destroy yet)
5. Notify stakeholders of rollback

**Verification:**
```bash
# Check that canary is receiving no traffic
curl -s https://app.example.com/health | jq '.version'
# Should show the old version

# Monitor error rate — should return to baseline within 1-2 minutes
```

---

### Blue-Green Rollback

**Time to recover:** < 1 minute (LB/DNS switch)

**Steps:**
1. Switch load balancer or DNS back to the old (previously active) environment
   - Load balancer: change target group to old environment
   - DNS: update CNAME to old environment endpoint
   - Kubernetes: update Service selector to old deployment
2. Confirm traffic is flowing to the old environment
3. Run smoke tests against production URL
4. Keep the new (failed) environment running for investigation
5. Notify stakeholders of rollback

**Verification:**
```bash
# Verify which environment is receiving traffic
curl -s https://app.example.com/health | jq '.environment'
# Should show "blue" or "green" (whichever is the old one)

# If using DNS, check propagation
dig app.example.com CNAME
```

**DNS Considerations:**
- If rollback is via DNS, recovery depends on TTL
- Set TTL to 60 seconds or less before deployment
- Some clients cache DNS beyond TTL; full recovery may take longer
- Prefer load balancer switching over DNS for faster rollback

---

### Rolling Update Rollback

**Time to recover:** 2-10 minutes (depends on pod count)

**Steps:**
1. Undo the deployment:
   ```bash
   kubectl rollout undo deployment/<NAME>
   ```
2. Monitor rollback progress:
   ```bash
   kubectl rollout status deployment/<NAME>
   ```
3. Watch pods to verify old version is restored:
   ```bash
   kubectl get pods -o wide -w
   ```
4. Run smoke tests once rollback is complete
5. Notify stakeholders of rollback

**Verification:**
```bash
# Verify deployment image is the old version
kubectl get deployment <NAME> -o jsonpath='{.spec.template.spec.containers[0].image}'

# Check no pods are in error state
kubectl get pods | grep -E 'Error|CrashLoopBackOff'

# Check rollout history
kubectl rollout history deployment/<NAME>
```

**Speeding Up Rolling Rollback:**
- Increase `maxSurge` temporarily to speed up pod replacement
- Reduce `terminationGracePeriodSeconds` if safe
- Scale down first, then roll back, then scale up (if downtime is acceptable)

---

### Recreate Rollback

**Time to recover:** 5-15 minutes (full redeployment)

**Steps:**
1. Redeploy the previous version's image/artifact
2. Wait for all instances to start and pass health checks
3. Run smoke tests
4. Notify stakeholders

**Note:** This strategy has the slowest rollback. Avoid using recreate in production.

---

## Database Rollback Considerations

Database changes are the most difficult to roll back because they may involve data that was written after the migration.

### Scenarios

#### Added a New Column (Safe)
- **Rollback:** No database change needed. The old code simply ignores the new column.
- **Cleanup:** Drop the column in a future deployment if the feature is abandoned.

#### Renamed or Removed a Column (Dangerous)
- **Rollback:** If the old code relies on the removed column, the rollback will fail.
- **Prevention:** Never remove or rename a column in the same deployment that removes code using it. Use the expand-contract pattern (see `deployment_strategies.md`).

#### Changed Data Format (Dangerous)
- **Rollback:** If data was written in the new format, the old code may not read it correctly.
- **Prevention:** Write a backward migration script. Test it before deploying. Accept that some data may need manual repair.

#### Added Data (Usually Safe)
- **Rollback:** New rows/records created post-deployment usually do not break old code.
- **Consideration:** If the new code created data that the old code cannot handle, you may need to clean it up.

### Database Rollback Checklist
- [ ] Was a database migration run as part of this deployment?
- [ ] Is the migration backward-compatible (old code works with new schema)?
- [ ] Do we have a rollback migration script ready?
- [ ] Has the rollback migration been tested on a copy of production data?
- [ ] Is there new data in the new schema that would be lost on rollback?
- [ ] Can the old code safely ignore the new schema elements?

---

## Post-Rollback Checklist

After any rollback, complete these steps:

### Immediate (First 15 Minutes)
- [ ] Confirm production is stable (error rate, latency, health checks)
- [ ] Run full smoke test suite against production
- [ ] Notify stakeholders that rollback is complete
- [ ] Check for data inconsistency from the partial deployment

### Short-Term (First Hour)
- [ ] Preserve logs and metrics from the failed deployment for investigation
- [ ] Capture the state of the failed environment (do not destroy yet)
- [ ] Write a brief summary of what happened and share with the team
- [ ] Determine if any user data was affected

### Investigation (Next 24-48 Hours)
- [ ] Identify root cause of the deployment failure
- [ ] Determine what the pre-deployment testing missed
- [ ] Update tests to catch the issue in the future
- [ ] Update deployment runbook with lessons learned
- [ ] Schedule redeployment once the fix is ready and tested

---

## Communication Template During Rollback

### When Rollback Starts
Post in the team incident channel immediately:

> **ROLLBACK IN PROGRESS**
>
> **Service:** {service_name}
> **Environment:** Production
> **Version:** v{new_version} being rolled back to v{old_version}
> **Reason:** {brief reason — e.g., "Error rate spiked to 5% after deployment"}
> **Lead:** {your name}
> **Status:** Rolling back now. ETA: {estimated time}.
>
> Please do NOT deploy any other services until this is resolved.

### When Rollback Is Complete
> **ROLLBACK COMPLETE**
>
> **Service:** {service_name}
> **Status:** Rolled back to v{old_version}. Production is stable.
> **Impact:** {description of user impact, if any}
> **Next Steps:** Root cause investigation in progress. Redeployment will be scheduled after fix is verified.
> **Incident Doc:** {link to incident document, if applicable}

### If User-Facing Impact Occurred
> **User Impact Notice**
>
> Between {start_time} and {end_time}, some users may have experienced {description of impact}. The issue has been resolved. If you continue to see problems, please report them to {channel/support}.

---

## Rollback Drills

Practice makes rollbacks reliable. Run rollback drills regularly:

### Monthly Drill
1. Deploy a known-safe "canary breaker" version to staging
2. Detect the issue via monitoring
3. Execute the rollback procedure
4. Time the entire process
5. Review and improve

### Drill Metrics to Track
| Metric | Target |
|--------|--------|
| Time to detect issue | < 2 minutes |
| Time to decide to roll back | < 3 minutes |
| Time to complete rollback | < 5 minutes (canary/BG), < 10 minutes (rolling) |
| Time to verify recovery | < 5 minutes |
| **Total recovery time** | **< 15 minutes** |

### After Each Drill
- Document what went well and what was slow
- Update the runbook if steps were unclear
- Automate any manual steps that caused delays
- Celebrate that the team practiced (this is important)
