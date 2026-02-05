---
name: requirements-planning
description: Elicit, document, and validate project requirements
version: 1.0.0
phase: 1
commands:
  - /plan [name]
---

# Phase 1: Requirements & Planning

## Purpose
Transform a project idea into a structured set of requirements with clear acceptance criteria. This phase prevents building the wrong thing — the #1 cause of project failure.

## Workflow

### Step 1: Elicit Requirements
Run the interactive requirement gathering script:
```bash
python skills/01-requirements/scripts/gather_requirements.py --project "ProjectName"
```
This walks through:
- Problem statement (what pain point are we solving?)
- Target users (who benefits?)
- Core features (what must it do?)
- Non-functional requirements (performance, security, scale)
- Constraints (timeline, budget, tech limitations)

### Step 2: Write PRD
Create `docs/prd.md` using the template:
```bash
cat skills/01-requirements/reference/prd_template.md
```

PRD must include:
1. Executive summary
2. Problem statement
3. Goals and non-goals
4. User stories with acceptance criteria
5. Technical requirements
6. Success metrics
7. Timeline and milestones

### Step 3: Define User Stories
Follow INVEST criteria (see `reference/user_story_guide.md`):
- **I**ndependent — no dependencies between stories
- **N**egotiable — details flexible until sprint
- **V**aluable — delivers user value
- **E**stimable — can be sized
- **S**mall — fits in one sprint
- **T**estable — has acceptance criteria

Format:
```
As a [user type], I want [action] so that [benefit].

Acceptance Criteria:
- Given [context], when [action], then [result]
- Given [context], when [action], then [result]
```

### Step 4: Validate Requirements
```bash
python skills/01-requirements/scripts/validate_prd.py --file docs/prd.md
```
Checks for completeness: problem statement, user stories, acceptance criteria, metrics.

### Step 5: Gate Check
```bash
python scripts/gate_validator.py --phase requirements
```

## Phase Exit Criteria
- [ ] PRD document exists
- [ ] User stories with acceptance criteria defined
- [ ] Technical feasibility assessed
- [ ] Success metrics defined
- [ ] Stakeholder sign-off recorded

## Reference Docs
- `reference/prd_template.md` — PRD template with examples
- `reference/user_story_guide.md` — User story writing guide

## Tips
- Start with "why" before "what" — understand the problem deeply
- Talk to actual users, not just stakeholders
- Define what you're NOT building (non-goals prevent scope creep)
- Acceptance criteria are your contract — make them testable
