#!/usr/bin/env python3
"""
Deployment Plan Generator — SDLC Orchestrator Phase 6

Generates a detailed step-by-step deployment runbook for the chosen strategy.
Includes pre-checks, deployment steps, verification steps, rollback steps,
and a communication template.

Usage:
    python deployment_plan.py --strategy canary --output docs/deployment-runbook.md
    python deployment_plan.py --strategy blue-green --service-name my-api --env production
    python deployment_plan.py --help
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


STRATEGIES = {
    "canary": {
        "name": "Canary Deployment",
        "description": "Gradually shift traffic from the old version to the new version, "
                       "monitoring for errors at each stage before increasing traffic.",
        "pre_checks": [
            "Verify canary infrastructure is provisioned (separate target group / pod subset)",
            "Confirm traffic splitting mechanism is operational (load balancer rules, service mesh)",
            "Validate monitoring dashboards are accessible and alerting is enabled",
            "Ensure current production is healthy (baseline error rate, latency, CPU/memory)",
            "Confirm deployment artifact is built, tested, and tagged",
            "Verify database migrations (if any) are backward-compatible",
            "Notify on-call engineer and stakeholders of deployment window",
        ],
        "steps": [
            "1. Tag the release: `git tag -a v<VERSION> -m 'Release v<VERSION>'`",
            "2. Deploy new version to canary instances (do NOT route traffic yet)",
            "3. Run smoke tests against canary instances directly (internal endpoint)",
            "4. Route **5%** of production traffic to canary",
            "5. Monitor for **5 minutes** — check error rate, latency p99, CPU",
            "6. If metrics are healthy, increase to **25%** traffic",
            "7. Monitor for **10 minutes**",
            "8. If metrics are healthy, increase to **50%** traffic",
            "9. Monitor for **10 minutes**",
            "10. If metrics are healthy, shift **100%** traffic to new version",
            "11. Decommission old instances after 30-minute bake period",
        ],
        "verification": [
            "Smoke tests pass against production URL",
            "Error rate is within baseline (< 0.1% or per SLO)",
            "Latency p50/p95/p99 within acceptable range",
            "No increase in 5xx responses",
            "Key business metrics are stable (conversion, sign-ups, etc.)",
            "Log aggregation shows no new error patterns",
        ],
        "rollback": [
            "1. Shift 100% traffic back to old (stable) instances immediately",
            "2. Confirm old instances are handling all traffic",
            "3. Run smoke tests against production URL",
            "4. Investigate root cause on canary instances (keep them running for debugging)",
            "5. Notify stakeholders of rollback and estimated redeployment time",
            "6. Once investigated, tear down canary instances",
        ],
        "estimated_duration": "30-60 minutes",
    },
    "blue-green": {
        "name": "Blue-Green Deployment",
        "description": "Maintain two identical production environments (blue and green). "
                       "Deploy to the inactive environment, verify it, then switch traffic "
                       "via DNS or load balancer. Rollback is instant — just switch back.",
        "pre_checks": [
            "Identify active environment (blue or green) and confirm it is healthy",
            "Verify inactive environment is provisioned and reachable",
            "Confirm DNS TTL is low enough for fast switchover (< 60s recommended)",
            "Validate load balancer / reverse proxy configuration for switching",
            "Ensure database schema is compatible with both old and new versions",
            "Confirm deployment artifact is built, tested, and tagged",
            "Notify on-call engineer and stakeholders of deployment window",
        ],
        "steps": [
            "1. Tag the release: `git tag -a v<VERSION> -m 'Release v<VERSION>'`",
            "2. Deploy new version to the **inactive** environment",
            "3. Run full smoke test suite against the inactive environment (direct URL)",
            "4. Run database migrations if needed (must be backward-compatible)",
            "5. Verify inactive environment is fully healthy (health endpoint, metrics)",
            "6. Switch load balancer / DNS to point to the **new** environment",
            "7. Confirm traffic is flowing to the new environment",
            "8. Run smoke tests against the production URL",
            "9. Monitor metrics for **15 minutes** (bake period)",
            "10. Keep old environment running for at least 1 hour as rollback target",
        ],
        "verification": [
            "Smoke tests pass against production URL post-switch",
            "No traffic reaching old environment (unless intentional drain)",
            "Error rate is within baseline",
            "Latency p50/p95/p99 within acceptable range",
            "Health checks all passing on new environment",
            "Business metrics stable",
        ],
        "rollback": [
            "1. Switch load balancer / DNS back to the **old** environment immediately",
            "2. Confirm traffic is flowing to the old environment",
            "3. Run smoke tests against production URL",
            "4. If database migrations were applied, run backward migration (if needed)",
            "5. Notify stakeholders of rollback",
            "6. Keep new (failed) environment for investigation before tearing down",
        ],
        "estimated_duration": "15-30 minutes",
    },
    "rolling": {
        "name": "Rolling Update Deployment",
        "description": "Gradually replace instances of the old version with the new version, "
                       "one (or a few) at a time. Native to Kubernetes and most container "
                       "orchestrators. No additional infrastructure needed.",
        "pre_checks": [
            "Verify current deployment is healthy (all pods/instances running)",
            "Confirm rolling update parameters: maxSurge, maxUnavailable",
            "Ensure readiness and liveness probes are configured correctly",
            "Validate that the new version is backward-compatible with current traffic",
            "Confirm deployment artifact is built, tested, and tagged",
            "Verify database migrations (if any) are backward-compatible",
            "Notify on-call engineer and stakeholders of deployment window",
        ],
        "steps": [
            "1. Tag the release: `git tag -a v<VERSION> -m 'Release v<VERSION>'`",
            "2. Update the deployment manifest (image tag, config changes)",
            "3. Apply the deployment: `kubectl apply -f deployment.yaml`",
            "4. Monitor rollout status: `kubectl rollout status deployment/<NAME>`",
            "5. Watch pods transitioning: `kubectl get pods -w`",
            "6. Verify each new pod passes readiness probe before continuing",
            "7. Wait for all old pods to terminate gracefully",
            "8. Run smoke tests against production URL",
            "9. Monitor metrics for **15 minutes** (bake period)",
        ],
        "verification": [
            "All pods are running the new version: `kubectl get pods -o wide`",
            "No pods in CrashLoopBackOff or Error state",
            "Readiness and liveness probes passing",
            "Smoke tests pass against production URL",
            "Error rate and latency within baseline",
            "No increase in pod restarts",
        ],
        "rollback": [
            "1. Rollback the deployment: `kubectl rollout undo deployment/<NAME>`",
            "2. Monitor rollback status: `kubectl rollout status deployment/<NAME>`",
            "3. Verify all pods are running the previous version",
            "4. Run smoke tests against production URL",
            "5. Notify stakeholders of rollback",
            "6. Investigate root cause using logs: `kubectl logs <POD> --previous`",
        ],
        "estimated_duration": "10-20 minutes",
    },
}


COMMUNICATION_TEMPLATE = """
## Communication Template

### Pre-Deployment Notification
> **Subject:** [Planned] Deployment of {service_name} v<VERSION> to {env}
>
> **When:** {timestamp}
> **What:** Deploying {service_name} v<VERSION> using {strategy} strategy
> **Impact:** Expected zero downtime. Users should not be affected.
> **Rollback:** Tested and ready. ETA for rollback: < 5 minutes.
> **Point of contact:** [YOUR NAME]

### Post-Deployment Notification
> **Subject:** [Complete] Deployment of {service_name} v<VERSION> to {env}
>
> **Status:** SUCCESS / ROLLED BACK
> **Duration:** <DURATION>
> **Notes:** <ANY ISSUES OR OBSERVATIONS>

### Rollback Notification
> **Subject:** [Rollback] {service_name} v<VERSION> on {env}
>
> **Status:** Rolled back to v<PREVIOUS_VERSION>
> **Reason:** <BRIEF DESCRIPTION>
> **Impact:** <USER IMPACT DESCRIPTION>
> **Next steps:** Investigation in progress. Follow-up deployment TBD.
""".strip()


def generate_runbook(strategy: str, service_name: str, env: str) -> str:
    """Generate a complete deployment runbook in markdown format."""
    config = STRATEGIES[strategy]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    sections = []

    # Header
    sections.append(f"# Deployment Runbook: {service_name}")
    sections.append("")
    sections.append(f"| Field | Value |")
    sections.append(f"|-------|-------|")
    sections.append(f"| **Service** | {service_name} |")
    sections.append(f"| **Environment** | {env} |")
    sections.append(f"| **Strategy** | {config['name']} |")
    sections.append(f"| **Generated** | {timestamp} |")
    sections.append(f"| **Estimated Duration** | {config['estimated_duration']} |")
    sections.append("")

    # Strategy overview
    sections.append(f"## Strategy: {config['name']}")
    sections.append("")
    sections.append(config["description"])
    sections.append("")

    # Pre-checks
    sections.append("## Pre-Deployment Checklist")
    sections.append("")
    for check in config["pre_checks"]:
        sections.append(f"- [ ] {check}")
    sections.append("")

    # Deployment steps
    sections.append("## Deployment Steps")
    sections.append("")
    for step in config["steps"]:
        sections.append(step)
    sections.append("")

    # Verification
    sections.append("## Post-Deployment Verification")
    sections.append("")
    for item in config["verification"]:
        sections.append(f"- [ ] {item}")
    sections.append("")

    # Rollback
    sections.append("## Rollback Procedure")
    sections.append("")
    sections.append("> **Trigger rollback if:** error rate > 1%, latency p99 > 2x baseline, "
                    "smoke tests fail, or any critical user-facing issue is detected.")
    sections.append("")
    for step in config["rollback"]:
        sections.append(step)
    sections.append("")

    # Communication template
    sections.append(COMMUNICATION_TEMPLATE.format(
        service_name=service_name,
        env=env,
        timestamp=timestamp,
        strategy=config["name"],
    ))
    sections.append("")

    # Sign-off
    sections.append("## Sign-Off")
    sections.append("")
    sections.append("| Role | Name | Approved |")
    sections.append("|------|------|----------|")
    sections.append("| Deploy Lead | | [ ] |")
    sections.append("| On-Call Engineer | | [ ] |")
    sections.append("| Product Owner | | [ ] |")
    sections.append("")

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a deployment runbook for a chosen deployment strategy.",
        epilog="Example: python deployment_plan.py --strategy canary --service-name my-api --env production",
    )
    parser.add_argument(
        "--strategy",
        required=True,
        choices=list(STRATEGIES.keys()),
        help="Deployment strategy to use (canary, blue-green, rolling)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for the runbook (default: print to stdout)",
    )
    parser.add_argument(
        "--service-name",
        type=str,
        default="my-service",
        help="Name of the service being deployed (default: my-service)",
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=["staging", "production"],
        default="production",
        help="Target environment (default: production)",
    )

    args = parser.parse_args()

    runbook = generate_runbook(
        strategy=args.strategy,
        service_name=args.service_name,
        env=args.env,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(runbook, encoding="utf-8")
        print(f"Deployment runbook written to {args.output}")
    else:
        print(runbook)


if __name__ == "__main__":
    main()
