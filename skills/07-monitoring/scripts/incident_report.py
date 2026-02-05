#!/usr/bin/env python3
"""
Incident Report Generator — Creates structured postmortem templates.

Generates a markdown incident report / postmortem template pre-populated with
date, severity, and incident description. Includes sections for timeline,
impact analysis, root cause, resolution, action items, and lessons learned.

Usage:
    python incident_report.py --incident "API latency spike" --severity P1 --output docs/incidents/
    python incident_report.py --incident "Database connection pool exhausted" --severity P0
    python incident_report.py --help
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone


SEVERITY_DEFINITIONS = {
    "P0": {
        "label": "P0 (Critical)",
        "description": "Complete outage. All users affected.",
        "response_time": "Immediate",
        "communication": "Every 15 minutes until resolved",
        "stakeholders": "VP Engineering, CTO, all on-call, customer support lead",
    },
    "P1": {
        "label": "P1 (High)",
        "description": "Major feature broken. Many users affected.",
        "response_time": "< 15 minutes",
        "communication": "Every 30 minutes until resolved",
        "stakeholders": "Engineering manager, on-call engineer, customer support",
    },
    "P2": {
        "label": "P2 (Medium)",
        "description": "Degraded service. Some users affected.",
        "response_time": "< 1 hour",
        "communication": "Every 2 hours until resolved",
        "stakeholders": "On-call engineer, team lead",
    },
    "P3": {
        "label": "P3 (Low)",
        "description": "Minor issue. Few users affected.",
        "response_time": "Next business day",
        "communication": "Daily update if unresolved",
        "stakeholders": "Assigned engineer",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a structured incident report / postmortem template.",
        epilog='Example: python incident_report.py --incident "API latency spike" --severity P1 --output docs/incidents/',
    )
    parser.add_argument(
        "--incident",
        type=str,
        required=True,
        help='Short description of the incident (e.g., "API latency spike")',
    )
    parser.add_argument(
        "--severity",
        type=str,
        required=True,
        choices=["P0", "P1", "P2", "P3"],
        help="Incident severity level (P0=Critical, P1=High, P2=Medium, P3=Low)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/incidents/",
        help="Output directory for the incident report (default: docs/incidents/)",
    )
    parser.add_argument(
        "--service",
        type=str,
        default="",
        help="Affected service name (optional)",
    )
    return parser.parse_args()


def slugify(text):
    """Convert text to a URL/filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def generate_report(incident, severity, service, now):
    """Generate the markdown content for an incident report."""
    sev = SEVERITY_DEFINITIONS[severity]
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M UTC")
    service_line = f"**Affected Service:** {service}" if service else "**Affected Service:** _[specify service]_"

    return f"""# Incident Report: {incident}

| Field | Value |
|-------|-------|
| **Date** | {date_str} |
| **Severity** | {sev["label"]} |
| **Status** | Open |
| **Incident Commander** | _[assign name]_ |
| **Report Author** | _[your name]_ |

{service_line}

---

## 1. Summary

**What happened:**
_[1-2 sentence description of the incident and its user-facing impact]_

> {incident}

**Severity justification:** {sev["description"]}

**Expected response time:** {sev["response_time"]}

**Communication cadence:** {sev["communication"]}

**Stakeholders notified:** {sev["stakeholders"]}

---

## 2. Timeline

All times in UTC. Be specific and factual.

| Time | Event |
|------|-------|
| {time_str} | Incident detected / reported |
| _HH:MM_ | _[First alert fired / user report received]_ |
| _HH:MM_ | _[Incident commander assigned]_ |
| _HH:MM_ | _[Initial investigation began]_ |
| _HH:MM_ | _[Root cause identified]_ |
| _HH:MM_ | _[Mitigation applied]_ |
| _HH:MM_ | _[Service restored]_ |
| _HH:MM_ | _[Incident resolved and closed]_ |

**Total duration:** _[detection to resolution]_
**Time to detect (TTD):** _[issue start to first alert]_
**Time to mitigate (TTM):** _[first alert to mitigation]_
**Time to resolve (TTR):** _[first alert to full resolution]_

---

## 3. Impact

### User Impact
- **Users affected:** _[number or percentage]_
- **Requests affected:** _[failed/degraded request count]_
- **Duration of impact:** _[minutes/hours]_
- **Regions affected:** _[all / specific regions]_

### Business Impact
- **Revenue impact:** _[estimated $ or "none"]_
- **SLA/SLO impact:** _[error budget consumed, SLA breach risk]_
- **Data loss:** _[yes/no, describe if yes]_
- **Reputational impact:** _[customer complaints, social media, etc.]_

### Technical Impact
- **Services affected:** _[list services]_
- **Dependencies impacted:** _[downstream services]_
- **Data integrity:** _[any corruption or inconsistency]_

---

## 4. Root Cause

### What caused the incident?
_[Describe the technical root cause. Be specific. Include the chain of events that led to the failure.]_

### Contributing factors
- _[Factor 1: e.g., missing monitoring for X]_
- _[Factor 2: e.g., insufficient load testing]_
- _[Factor 3: e.g., single point of failure in Y]_

### Why was it not caught earlier?
_[Describe gaps in testing, monitoring, or review that allowed this to reach production.]_

---

## 5. Resolution

### Immediate mitigation
_[What was done to stop the bleeding? e.g., rollback, config change, traffic reroute]_

### Permanent fix
_[What is the long-term fix? Link to PR/ticket if available.]_

### Verification
_[How was the fix verified? What metrics confirmed recovery?]_

---

## 6. Action Items

Track each action item to completion. Every action item must have an owner and a due date.

| Priority | Action Item | Owner | Due Date | Status |
|----------|-------------|-------|----------|--------|
| High | _[Prevent recurrence: e.g., add circuit breaker]_ | _[name]_ | _[date]_ | TODO |
| High | _[Improve detection: e.g., add alert for X]_ | _[name]_ | _[date]_ | TODO |
| Medium | _[Improve resilience: e.g., add retry logic]_ | _[name]_ | _[date]_ | TODO |
| Medium | _[Update runbook for this scenario]_ | _[name]_ | _[date]_ | TODO |
| Low | _[Improve testing: e.g., add chaos test]_ | _[name]_ | _[date]_ | TODO |

---

## 7. Lessons Learned

### What went well
- _[e.g., alert fired quickly, team responded within SLA]_
- _[e.g., rollback process worked smoothly]_
- _[e.g., communication was clear and timely]_

### What went poorly
- _[e.g., took too long to identify root cause]_
- _[e.g., runbook was outdated]_
- _[e.g., no monitoring for the specific failure mode]_

### Where we got lucky
- _[e.g., happened during low-traffic period]_
- _[e.g., expert happened to be online]_

---

## 8. Appendix

### Related Links
- Monitoring dashboard: _[URL]_
- Alert that fired: _[URL]_
- Relevant PRs: _[URLs]_
- Related tickets: _[URLs]_

### Communication Log
- _[Link to Slack thread / incident channel]_
- _[Link to status page update]_

---

> **Reminder:** This is a *blameless* postmortem. The goal is to improve systems and
> processes, not to assign blame. Focus on what the *system* allowed to happen and how
> we can make the *system* more resilient.
>
> Review this report with the team within 5 business days of the incident.
"""


def main():
    args = parse_args()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    slug = slugify(args.incident)

    os.makedirs(args.output, exist_ok=True)

    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(args.output, filename)

    # Avoid overwriting existing reports
    if os.path.exists(filepath):
        counter = 2
        while os.path.exists(filepath):
            filename = f"{date_str}-{slug}-{counter}.md"
            filepath = os.path.join(args.output, filename)
            counter += 1

    content = generate_report(args.incident, args.severity, args.service, now)

    with open(filepath, "w") as f:
        f.write(content)

    sev = SEVERITY_DEFINITIONS[args.severity]
    print(f"Incident report generated:")
    print(f"  Incident:  {args.incident}")
    print(f"  Severity:  {sev['label']}")
    print(f"  Date:      {date_str}")
    print(f"  Output:    {filepath}")
    print()
    print(f"Next steps:")
    print(f"  1. Fill in the timeline with exact timestamps")
    print(f"  2. Document root cause and contributing factors")
    print(f"  3. Assign owners and due dates to all action items")
    print(f"  4. Schedule a blameless postmortem review within 5 business days")


if __name__ == "__main__":
    main()
