# Incident Response Playbook

This reference covers incident management from detection to postmortem, including severity definitions, roles, communication, and proactive resilience practices.

---

## Incident Severity Definitions

| Severity | Name | Description | Response Time | Examples |
|----------|------|-------------|---------------|----------|
| **P0** | Critical | Complete outage. All or most users affected. Core business function is down. | Immediate (all hands) | Total site down, data breach, payment processing failure. |
| **P1** | High | Major feature broken. Many users affected. Significant business impact. | < 15 minutes | Login broken, search returns no results, major API degraded. |
| **P2** | Medium | Degraded service. Some users affected. Workaround may exist. | < 1 hour | Slow page loads, intermittent errors on a non-critical feature, one region degraded. |
| **P3** | Low | Minor issue. Few users affected. Minimal business impact. | Next business day | Cosmetic bug, minor feature broken for a small user segment, non-critical alert. |

### Escalation Rules

- **P0:** Automatically pages all on-call engineers plus engineering leadership. External status page updated within 10 minutes.
- **P1:** Pages primary on-call. If not acknowledged within 10 minutes, escalates to secondary on-call and engineering manager.
- **P2:** Notifies on-call via chat. If not acknowledged within 30 minutes, pages on-call.
- **P3:** Creates a ticket. No page. Addressed during normal working hours.

---

## On-Call Rotation Setup

### Principles

1. **Shared responsibility.** Everyone who writes code should participate in on-call. This creates incentive to write reliable software.
2. **Sustainable shifts.** 1-week rotations with no more than 1 in 4 weeks on-call. Handoffs happen on weekday mornings, not Fridays.
3. **Compensation.** On-call engineers receive additional compensation or time off. Uncompensated on-call leads to burnout and attrition.
4. **Tooling.** Use a paging tool (PagerDuty, Opsgenie, Grafana OnCall) with automatic escalation policies.

### Rotation Structure

```
Primary On-Call (1 person)
  |
  +--> Escalation after 10 min: Secondary On-Call (1 person)
         |
         +--> Escalation after 10 min: Engineering Manager
                |
                +--> Escalation after 15 min: VP Engineering
```

### Handoff Checklist

At the start of each rotation, the outgoing on-call should brief the incoming on-call:

- [ ] Active incidents or lingering issues
- [ ] Recent deployments and known risks
- [ ] Noisy alerts that can be safely ignored (with plan to fix them)
- [ ] Any pending maintenance windows
- [ ] Status of error budget (how much is remaining)

---

## Incident Commander Role

The Incident Commander (IC) is the single person responsible for coordinating the incident response. The IC does not need to be the most senior person or the person who will fix the issue.

### Responsibilities

1. **Declare the incident.** Assign a severity level and create a dedicated communication channel (e.g., Slack channel `#incident-YYYY-MM-DD-slug`).
2. **Assign roles.** Designate who is investigating, who is communicating, and who is scribing (recording the timeline).
3. **Coordinate, do not fix.** The IC's job is to remove blockers and coordinate efforts, not to debug code. If the IC is the only person who can fix it, hand off IC duties to someone else.
4. **Manage communication.** Ensure internal stakeholders and external customers receive timely updates.
5. **Make decisions.** The IC has authority to roll back deployments, disable features, or scale infrastructure.
6. **Close the incident.** Declare when the incident is resolved, schedule the postmortem, and ensure action items are tracked.

### IC Rotation

- For P0/P1: The on-call engineer becomes IC by default. They can hand off to another person.
- For P2: The on-call engineer handles it without a formal IC role.
- For P3: No IC needed.

---

## Communication Templates

### Internal Update (Post to Slack / Incident Channel)

```
**Incident Update — [SEVERITY] — [SHORT TITLE]**
**Time:** YYYY-MM-DD HH:MM UTC
**Status:** Investigating / Identified / Mitigating / Resolved
**Incident Commander:** [Name]

**Summary:**
[1-2 sentences: what is broken and who is affected.]

**Current Actions:**
- [What is being done right now]
- [Who is working on what]

**Next Update:** [time of next planned update, e.g., "in 30 minutes"]
```

### External Status Page Update

**Investigating:**
```
We are investigating reports of [description of user-facing impact].
Some users may experience [specific symptoms]. We are working to
identify the cause and will provide updates as we learn more.
```

**Identified:**
```
We have identified the cause of [issue description]. Our team is
working on a fix. [Specific services] are affected. We expect to
provide an update within [timeframe].
```

**Mitigating:**
```
A fix has been applied and we are monitoring the results. [Service]
performance is improving. Some users may still experience [residual
impact] for the next [timeframe].
```

**Resolved:**
```
This incident has been resolved. [Service] is operating normally.
The issue was caused by [brief, non-technical explanation]. We will
publish a full postmortem within [timeframe]. We apologize for
the inconvenience.
```

---

## Blameless Postmortem Process

The postmortem is the most valuable part of incident response. Done well, it turns every incident into a systemic improvement. Done poorly (or not at all), the same incidents repeat.

### Core Principles

1. **Blameless.** People do not cause incidents; systems allow them. If a human made an error, ask why the system allowed that error to have impact.
2. **Thorough.** Investigate the full causal chain. Do not stop at the proximate cause ("bad deploy") — dig into the contributing factors ("no canary process, no automated rollback, no test for this case").
3. **Action-oriented.** Every postmortem must produce concrete, tracked action items with owners and due dates. A postmortem without action items is just a story.
4. **Timely.** Hold the review meeting within 5 business days of the incident. Memories fade quickly.
5. **Shared.** Publish postmortems internally. Other teams learn from your incidents. Consider publishing externally for major incidents (many respected companies do this).

### Postmortem Meeting Agenda (60 minutes)

| Time | Activity |
|------|----------|
| 0-5 min | IC presents the timeline (facts only, no analysis). |
| 5-20 min | Group reviews the timeline and fills in gaps. |
| 20-35 min | Discuss root cause and contributing factors. Use "5 Whys" to dig deeper. |
| 35-45 min | Discuss what went well and what went poorly. |
| 45-55 min | Define action items. Assign owners and due dates. |
| 55-60 min | Agree on follow-up schedule for action items. |

### The 5 Whys Technique

Start with the symptom and ask "why" repeatedly until you reach the systemic cause:

1. **Why** did the site go down? -> The database ran out of connections.
2. **Why** did it run out of connections? -> A new feature opened connections without closing them.
3. **Why** was this not caught? -> There was no load test for the new feature.
4. **Why** was there no load test? -> The team has no standard process for load testing new features.
5. **Why** is there no standard process? -> Load testing was never prioritized or documented.

**Root cause:** Missing load testing process. **Action item:** Create a load testing standard and add it to the Definition of Done.

### Using the Incident Report Generator

```bash
python skills/07-monitoring/scripts/incident_report.py \
  --incident "Database connection pool exhausted" \
  --severity P1 \
  --service "payment-api" \
  --output docs/incidents/
```

This generates a pre-structured markdown template. Fill it in during or after the postmortem meeting.

---

## Action Item Tracking

Action items from postmortems are worthless if they are not tracked to completion.

### Categories

| Category | Description | Examples |
|----------|-------------|---------|
| **Prevent** | Stop this specific failure from recurring. | Add connection pool limits, fix the bug, add input validation. |
| **Detect** | Catch it faster next time. | Add missing alert, improve dashboard, add health check. |
| **Mitigate** | Reduce blast radius. | Add circuit breaker, implement graceful degradation, add rate limiting. |
| **Process** | Improve the response process itself. | Update runbook, improve on-call handoff, add chaos test. |

### Tracking Rules

1. Every action item gets a ticket in your issue tracker (Jira, Linear, GitHub Issues).
2. Tag tickets with `postmortem` and the incident ID.
3. Action items have a due date (not "someday").
4. Review open postmortem action items weekly in team standup.
5. Report on postmortem action item completion rate monthly. Below 80% completion signals a process problem.

---

## Chaos Engineering

Chaos engineering is the practice of intentionally injecting failures into production (or staging) systems to discover weaknesses before they cause real incidents.

### Principles

1. **Start with a hypothesis.** "We believe that if [failure X] occurs, [system Y] will [gracefully degrade / recover / etc.]."
2. **Minimize blast radius.** Start small. Test one failure at a time. Use feature flags and kill switches.
3. **Run in production.** Staging environments do not replicate production behavior. When your confidence grows, graduate experiments to production.
4. **Automate.** Manual chaos is better than no chaos, but automated experiments run consistently and often.

### Common Experiments

| Experiment | What It Tests | Tools |
|------------|---------------|-------|
| Kill a container/pod | Auto-recovery, load balancing | Chaos Monkey, LitmusChaos, `kubectl delete pod` |
| Inject network latency | Timeout handling, circuit breakers | Toxiproxy, Chaos Mesh, tc (Linux) |
| Simulate DNS failure | Fallback behavior, caching | Chaos Mesh, custom iptables rules |
| Fill disk | Log rotation, disk space alerts | Stress tools, dd |
| Exhaust CPU/memory | Autoscaling, resource limits, OOM handling | stress-ng, Chaos Mesh |
| Revoke database credentials | Connection pool recovery, secret rotation | Manual, custom scripts |
| Kill an availability zone | Multi-AZ resilience | AWS FIS, Gremlin |

### Getting Started

1. **Pick your most critical service.** Not the least critical — you want to find the important weaknesses.
2. **Start with a kill-one-pod experiment** in staging. Observe what happens. Does the service recover? How long does it take?
3. **Add monitoring** to observe the experiment. You cannot learn from chaos if you cannot see what happened.
4. **Gradually increase scope.** Pod -> node -> AZ -> region.
5. **Make it routine.** Schedule experiments weekly or bi-weekly. If chaos is a one-time event, it provides one-time value.

---

## Game Day Planning

A Game Day is a scheduled event where the team practices responding to simulated incidents. It builds muscle memory so that when a real incident occurs, the response is fast and calm.

### Format

| Phase | Duration | Activity |
|-------|----------|----------|
| Briefing | 15 min | Explain the scenario (or keep it a surprise). Review roles and communication channels. |
| Simulation | 30-60 min | Inject the failure. Team follows the incident response process. IC coordinates. Scribe records timeline. |
| Debrief | 30 min | Review what happened. What went well? What was confusing? Update runbooks and processes. |

### Sample Scenarios

1. **Database failover.** Simulate primary database going down. Test: Does the replica promote? Does the app reconnect?
2. **Dependency outage.** Block traffic to a critical third-party API. Test: Does the circuit breaker fire? Is the user experience gracefully degraded?
3. **Deployment gone wrong.** Deploy a known-bad version. Test: Do alerts fire? How quickly can the team roll back?
4. **Secret rotation.** Rotate a database password. Test: Does the service pick up the new credentials without downtime?
5. **Traffic spike.** Send 10x normal traffic to the service. Test: Does autoscaling work? Are rate limits effective?

### Tips

- Run Game Days quarterly at minimum.
- Rotate the IC role so everyone gets practice.
- Include non-engineering stakeholders (support, product) for P0 simulations so they practice their communication roles.
- Document findings and update runbooks immediately after.

---

## Runbook Template

Every alert should link to a runbook. A runbook provides step-by-step instructions so that any on-call engineer (not just the person who wrote the code) can respond effectively.

```markdown
# Runbook: [Alert Name]

## Alert Description
[What this alert means. What SLO/SLI it protects.]

## Severity
[Critical / Warning / Info]

## Likely Causes
1. [Cause A — e.g., traffic spike]
2. [Cause B — e.g., bad deploy]
3. [Cause C — e.g., dependency failure]

## Investigation Steps
1. Check the dashboard: [link]
2. Check recent deploys: [link to deploy log]
3. Check dependency status: [link to status page]
4. Check logs: [query to run in log tool]

## Mitigation Steps
- **If caused by bad deploy:** Roll back with `[rollback command]`.
- **If caused by traffic spike:** Scale up with `[scale command]`.
- **If caused by dependency failure:** Enable fallback with `[feature flag command]`.

## Escalation
- If unresolved after 15 minutes, escalate to [team/person].
- If data loss is suspected, notify [person/team].

## Related
- Architecture doc: [link]
- Previous incidents: [links]
```

---

## SRE Book Recommendations

These are the foundational texts for building reliable systems.

### Essential Reading

1. **Site Reliability Engineering** (Betsy Beyer et al., Google, 2016)
   The original "SRE Book." Covers SLOs, error budgets, on-call, incident management, monitoring, and release engineering. Free to read at [sre.google/sre-book](https://sre.google/sre-book/).

2. **The Site Reliability Workbook** (Betsy Beyer et al., Google, 2018)
   Practical companion to the SRE Book with hands-on examples. Free at [sre.google/workbook](https://sre.google/workbook/).

3. **Building Secure & Reliable Systems** (Heather Adkins et al., Google, 2020)
   Covers the intersection of security and reliability. Free at [sre.google/books](https://sre.google/books/).

### Highly Recommended

4. **Observability Engineering** (Charity Majors, Liz Fong-Jones, George Miranda, 2022)
   Modern take on observability beyond the three pillars. Covers high-cardinality data, debugging in production, and building an observability culture.

5. **Implementing Service Level Objectives** (Alex Hidalgo, 2020)
   Deep dive into SLOs, SLIs, and error budgets. The most practical guide to implementing SLOs in real organizations.

6. **Chaos Engineering** (Casey Rosenthal, Nora Jones, 2020)
   Comprehensive guide to chaos engineering principles and practices. From Netflix's Chaos Monkey to modern chaos platforms.

7. **Incident Management for Operations** (Rob Schnepp et al., 2017)
   Based on the Incident Command System used by first responders. Applicable, proven framework for tech incident management.

### Also Valuable

8. **The Phoenix Project** (Gene Kim et al., 2013) — Novel format. Introduces DevOps and SRE thinking through a story. Great for non-technical stakeholders.

9. **Accelerate** (Nicole Forsgren et al., 2018) — Research-backed metrics for software delivery performance (DORA metrics: deployment frequency, lead time, change failure rate, MTTR).

10. **Release It!** (Michael Nygard, 2nd ed. 2018) — Patterns for building resilient, production-ready systems. Circuit breakers, bulkheads, timeouts, and more.
