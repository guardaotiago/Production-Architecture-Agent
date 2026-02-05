# PRD: [Project Name]

> **Author:** [Your Name]
> **Date:** [YYYY-MM-DD]
> **Status:** Draft | In Review | Approved
> **Version:** 0.1

---

## 1. Executive Summary

_One paragraph describing what we are building and why it matters._

[Example: We are building a task management API that enables teams to track work items across projects. This replaces the current spreadsheet-based workflow, reducing manual overhead by an estimated 60% and providing real-time visibility into team progress.]

## 2. Problem Statement

_What problem exists today? Who is affected? What happens if we do nothing?_

**Current state:** [Describe how things work today]

**Pain points:**
- [Pain point 1]
- [Pain point 2]
- [Pain point 3]

**Impact of inaction:** [What happens if we don't solve this]

[Example: Teams currently track tasks in shared spreadsheets. Updates are manual, version conflicts are common, and managers lack real-time visibility. Without intervention, as the team grows from 10 to 50 people, this process will become unmanageable.]

## 3. Goals & Non-Goals

### Goals
- [Goal 1 — measurable outcome]
- [Goal 2 — measurable outcome]
- [Goal 3 — measurable outcome]

### Non-Goals
_Explicitly state what this project will NOT do. This prevents scope creep._
- [Non-goal 1]
- [Non-goal 2]

[Example Goals: Reduce task update time from 5 minutes to 30 seconds. Provide real-time dashboards for managers.]
[Example Non-Goals: We will NOT build a full project management suite. We will NOT replace email notifications.]

## 4. User Personas

### Persona 1: [Name / Role]
- **Who:** [Brief description]
- **Needs:** [What they need from this product]
- **Frustrations:** [Current pain points]

### Persona 2: [Name / Role]
- **Who:** [Brief description]
- **Needs:** [What they need from this product]
- **Frustrations:** [Current pain points]

## 5. User Stories

### Epic: [Epic Name]

#### Story 1: [Short title]
As a [user type], I want [action] so that [benefit].

**Acceptance Criteria:**
- Given [context], when [action], then [result]
- Given [context], when [action], then [result]

**Priority:** P0 (must-have) | P1 (should-have) | P2 (nice-to-have)

#### Story 2: [Short title]
As a [user type], I want [action] so that [benefit].

**Acceptance Criteria:**
- Given [context], when [action], then [result]
- Given [context], when [action], then [result]

**Priority:** P0 | P1 | P2

### Epic: [Epic Name]

#### Story 3: [Short title]
As a [user type], I want [action] so that [benefit].

**Acceptance Criteria:**
- Given [context], when [action], then [result]

**Priority:** P0 | P1 | P2

## 6. Technical Requirements

### Architecture
- [High-level architecture description]
- [Key technology choices and rationale]

### Tech Stack
| Layer      | Technology     | Rationale              |
|------------|----------------|------------------------|
| Frontend   | [e.g., React]  | [Why this choice]      |
| Backend    | [e.g., FastAPI]| [Why this choice]      |
| Database   | [e.g., Postgres]| [Why this choice]     |
| Hosting    | [e.g., AWS]    | [Why this choice]      |

### API Requirements
- [Endpoint patterns, auth mechanism, rate limits]

### Data Requirements
- [Data models, storage estimates, retention policy]

### Non-Functional Requirements
| Requirement    | Target                          |
|----------------|---------------------------------|
| Response time  | [e.g., < 200ms at p95]         |
| Availability   | [e.g., 99.9% uptime]           |
| Concurrency    | [e.g., 1000 concurrent users]  |
| Data security  | [e.g., encryption at rest, TLS]|

## 7. Success Metrics

_How will we know this project succeeded? Define measurable outcomes._

| Metric                  | Target         | How Measured             |
|-------------------------|----------------|--------------------------|
| [e.g., User adoption]  | [e.g., 80%]   | [e.g., weekly active users] |
| [e.g., Task update time]| [e.g., < 30s] | [e.g., P95 latency]     |
| [e.g., Error rate]     | [e.g., < 1%]  | [e.g., monitoring dashboard] |

## 8. Timeline & Milestones

| Milestone          | Date       | Deliverable                 |
|--------------------|------------|-----------------------------|
| Requirements done  | [Date]     | Approved PRD                |
| Design complete    | [Date]     | Architecture + API spec     |
| MVP ready          | [Date]     | Core features working       |
| Beta launch        | [Date]     | Internal testing complete   |
| GA release         | [Date]     | Production deployment       |

## 9. Open Questions

_Track unresolved questions here. Assign owners and target resolution dates._

| # | Question                        | Owner   | Target Date | Resolution |
|---|---------------------------------|---------|-------------|------------|
| 1 | [Open question]                 | [Name]  | [Date]      |            |
| 2 | [Open question]                 | [Name]  | [Date]      |            |

## 10. Appendix

### References
- [Link to related docs, research, competitor analysis]

### Revision History
| Version | Date       | Author   | Changes          |
|---------|------------|----------|------------------|
| 0.1     | [Date]     | [Author] | Initial draft    |
