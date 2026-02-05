---
name: user-acceptance-testing
description: UAT coordination, test execution, and stakeholder sign-off
version: 1.0.0
phase: 5
commands:
  - /uat
---

# Phase 5: User Acceptance Testing

## Purpose
Validate that the software meets business requirements from the end-user perspective. UAT is the final quality gate before production — stakeholders confirm the product is ready.

## Workflow

### Step 1: Generate UAT Plan
```bash
python skills/05-uat/scripts/generate_uat_plan.py --prd docs/prd.md --output docs/uat-plan.md
```
Converts user stories and acceptance criteria into structured UAT test cases with business-friendly language.

### Step 2: Prepare UAT Environment
- Mirror production configuration as closely as possible
- Load representative test data (anonymized if needed)
- Ensure all integrations are connected
- Verify environment stability before inviting testers

### Step 3: Brief Stakeholders
Communicate to UAT participants:
- Scope: what's being tested and what's out of scope
- Timeline: testing window and feedback deadline
- Process: how to report issues (template provided)
- Expectations: what constitutes a pass vs. block

### Step 4: Execute UAT Test Cases
Each test case follows:
```
ID: UAT-001
User Story: As a [user], I want [action] so that [benefit]
Precondition: [setup required]
Steps:
  1. [action]
  2. [action]
Expected Result: [what should happen]
Actual Result: [filled by tester]
Status: PASS | FAIL | BLOCKED
Notes: [observations]
```

### Step 5: Triage Feedback
Categorize issues:
- **Blocker**: Cannot ship. Must fix before deployment.
- **Major**: Significant UX issue. Fix if possible, defer if time-constrained.
- **Minor**: Cosmetic or low-impact. Can ship, fix in next iteration.
- **Enhancement**: Out of scope. Add to backlog.

### Step 6: Obtain Sign-off
Stakeholder sign-off confirms:
- All critical user journeys work as expected
- No blocker issues remain open
- The product meets the acceptance criteria from the PRD

### Step 7: Gate Check
```bash
python scripts/gate_validator.py --phase uat
```

## Phase Exit Criteria
- [ ] UAT plan created from user stories
- [ ] UAT environment provisioned and stable
- [ ] All UAT test cases executed
- [ ] Feedback triaged, blockers resolved
- [ ] Stakeholder sign-off obtained

## Reference Docs
- `reference/uat_best_practices.md` — Execution tips and stakeholder communication
