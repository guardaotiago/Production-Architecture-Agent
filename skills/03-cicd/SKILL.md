---
name: cicd-pipeline
description: Set up and manage CI/CD pipelines for automated build, test, and deploy
version: 1.0.0
phase: 3
commands:
  - /cicd [platform]
---

# Phase 3: CI/CD Pipeline

## Purpose
Automate the build-test-deploy cycle so every code change is validated before reaching production. CI/CD is the backbone of reliable software delivery.

## Workflow

### Step 1: Choose Platform
Supported platforms:
- **GitHub Actions** (default) -- native to GitHub, YAML-based
- **GitLab CI** -- built into GitLab, `.gitlab-ci.yml`
- **Jenkins** -- self-hosted, Groovy-based Jenkinsfile

### Step 2: Generate Pipeline Config
```bash
python skills/03-cicd/scripts/generate_pipeline.py --platform github --type node|python|go
```
Generates a production-ready pipeline with: build, test, lint, security scan, and deploy stages.

### Step 3: Configure Pipeline Stages
Standard pipeline stages:

1. **Install** -- install dependencies
2. **Lint** -- code style and quality checks
3. **Test** -- unit tests with coverage
4. **Security** -- SAST scanning (e.g., Trivy, Bandit, npm audit)
5. **Build** -- compile/bundle application
6. **Publish** -- push Docker image or package artifact
7. **Deploy** -- deploy to target environment (staging/production)

### Step 4: Set Up Docker (if applicable)
Templates available in `assets/docker/`:
- `Dockerfile.node` -- multi-stage Node.js build
- `Dockerfile.python` -- Python with slim base
- `docker-compose.yml` -- local development services

### Step 5: Branch Protection
Configure branch protection rules:
- Require PR reviews before merge
- Require status checks to pass
- Require up-to-date branches
- No force pushes to main

### Step 6: Gate Check
```bash
python scripts/gate_validator.py --phase cicd
```

## Phase Exit Criteria
- [ ] CI pipeline runs on every push
- [ ] Build and test steps configured
- [ ] Linting enforced in pipeline
- [ ] Security scanning active
- [ ] Pipeline verified end-to-end

## Reference Docs
- `reference/pipeline_patterns.md` -- Common pipeline patterns and best practices

## Assets
- `assets/github-actions/` -- GitHub Actions workflow templates
- `assets/docker/` -- Dockerfile and docker-compose templates
