---
name: qa-testing
description: QA testing strategy, test planning, and coverage analysis
version: 1.0.0
phase: 4
commands:
  - /test [type]
---

# Phase 4: QA Testing

## Purpose
Systematically verify that the software works correctly, performs well, and handles edge cases. Testing is not just about finding bugs — it's about building confidence.

## Workflow

### Step 1: Generate Test Plan
```bash
python skills/04-testing/scripts/test_planner.py --prd docs/prd.md --output docs/test-plan.md
```
Reads user stories and acceptance criteria from the PRD to generate a structured test plan with test cases grouped by: unit, integration, E2E, and performance.

### Step 2: Follow the Testing Pyramid
See `reference/testing_pyramid.md` for strategy:

```
        /  E2E  \        Few, slow, high confidence
       /----------\
      / Integration \    Some, medium speed
     /----------------\
    /    Unit Tests     \  Many, fast, focused
```

- **Unit tests** (70%): Test individual functions/modules in isolation
- **Integration tests** (20%): Test component interactions
- **E2E tests** (10%): Test full user journeys in browser/app

### Step 3: Write & Run Tests
```bash
# By type
/test unit          # Run unit tests only
/test integration   # Run integration tests
/test e2e          # Run end-to-end tests
/test all          # Run everything
```

### Step 4: Analyze Coverage
```bash
python skills/04-testing/scripts/coverage_analyzer.py --report coverage/lcov.info
```
Identifies:
- Uncovered functions and branches
- Critical paths without tests
- Coverage trends over time
- Recommendations for high-impact tests to add

### Step 5: Performance Testing
See `reference/performance_testing.md` for load/stress testing guidance.

### Step 6: Gate Check
```bash
python scripts/gate_validator.py --phase testing
```

## Phase Exit Criteria
- [ ] Unit test coverage >= 80%
- [ ] Integration tests for critical paths
- [ ] E2E tests for key user journeys
- [ ] Performance tests executed
- [ ] All critical/high bugs resolved
- [ ] Test coverage report generated

## Reference Docs
- `reference/testing_pyramid.md` -- Testing strategy and pyramid
- `reference/performance_testing.md` -- Load and stress testing guide
