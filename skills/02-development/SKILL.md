---
name: development-git
description: Development workflow, git conventions, and code quality
version: 1.0.0
phase: 2
commands:
  - /develop
---

# Phase 2: Development & Git

## Purpose
Establish a productive development workflow with clean version control practices. Good git hygiene now saves hours of debugging later.

## Workflow

### Step 1: Initialize Project
```bash
bash skills/02-development/scripts/init_project.sh --name "project-name" --type node|python|go
```
Sets up: directory structure, .gitignore, .editorconfig, README skeleton.

### Step 2: Configure Git Hooks
```bash
bash skills/02-development/scripts/setup_git_hooks.sh
```
Installs pre-commit hooks for: lint check, format check, secrets scan, commit message validation.

### Step 3: Follow Branching Strategy
See `reference/git_workflow.md` for full guide. Summary:
- `main` -- production-ready, protected
- `develop` -- integration branch (optional for smaller teams)
- `feature/TICKET-description` -- feature work
- `fix/TICKET-description` -- bug fixes
- `release/vX.Y.Z` -- release prep

### Step 4: Write Code
- Keep PRs small (< 400 lines changed)
- Write self-documenting code with meaningful names
- Add tests alongside features
- Document non-obvious decisions with comments

### Step 5: Commit Conventions
Follow Conventional Commits (see `reference/commit_conventions.md`):
```
type(scope): description

[optional body]
[optional footer]
```
Types: feat, fix, docs, style, refactor, test, chore, perf, ci

### Step 6: Code Review
Every PR must be reviewed before merge. Reviewer checks:
- Correctness -- does it do what it should?
- Style -- follows project conventions?
- Tests -- adequate coverage?
- Security -- no vulnerabilities introduced?

### Step 7: Gate Check
```bash
python scripts/gate_validator.py --phase development
```

## Phase Exit Criteria
- [ ] Git repo initialized with branching strategy
- [ ] Pre-commit hooks configured
- [ ] README with setup instructions exists
- [ ] Core features implemented
- [ ] Code reviewed and approved

## Reference Docs
- `reference/git_workflow.md` -- Branching strategy guide
- `reference/commit_conventions.md` -- Conventional commits specification
