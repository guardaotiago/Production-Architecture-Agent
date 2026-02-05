# CI/CD Pipeline Patterns & Best Practices

Reference guide for common pipeline patterns, optimization strategies, and operational best practices.

---

## Matrix Builds

Run the same job across multiple environments in parallel to catch compatibility issues early.

**When to use:** libraries, packages, or services that must support multiple runtime versions.

```yaml
# GitHub Actions example
strategy:
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, macos-latest]
  fail-fast: false  # let all combinations finish even if one fails
```

Tips:
- Use `fail-fast: false` during development to see all failures at once.
- Include/exclude specific combinations to avoid unnecessary runs.
- Keep the matrix small in PRs and expand it for nightly builds.

---

## Caching Strategies

Cache dependencies and build artifacts to reduce pipeline duration.

### Dependency Caching

| Ecosystem | Cache Key                  | Cache Path             |
|-----------|----------------------------|------------------------|
| Node.js   | `package-lock.json` hash   | `~/.npm` or `node_modules` |
| Python    | `requirements.txt` hash    | `~/.cache/pip`         |
| Go        | `go.sum` hash              | `~/go/pkg/mod`         |

```yaml
# GitHub Actions -- built-in cache for setup-node
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: npm
```

### Build Caching

- **Docker layer caching** -- use `docker/build-push-action` with `cache-from` / `cache-to`.
- **Incremental builds** -- tools like `turbo`, `nx`, or `gradle` support remote caching.
- Avoid caching test results or coverage reports (stale data hides regressions).

---

## Artifact Management

### Short-lived Artifacts (CI)

Upload test reports, coverage files, and build outputs as pipeline artifacts.

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: coverage/
    retention-days: 14
```

### Long-lived Artifacts (CD)

Publish versioned artifacts to a registry:
- **Docker images** -- push to GHCR, Docker Hub, ECR, or GCR.
- **NPM packages** -- publish to npm or a private registry.
- **Python packages** -- publish to PyPI or a private index.
- Tag every artifact with the git SHA and semantic version.

---

## Secrets Handling

### Principles

1. **Never commit secrets** -- use environment variables or secrets managers.
2. **Least privilege** -- grant only the permissions each job needs.
3. **Rotate regularly** -- automate rotation where possible.
4. **Audit access** -- log who/what accesses secrets and when.

### Platform Specifics

| Platform       | Mechanism                          |
|----------------|------------------------------------|
| GitHub Actions | Repository / environment secrets   |
| GitLab CI      | CI/CD variables (masked, protected)|
| Jenkins        | Credentials plugin                 |

### Secret Scanning

Run secret detection in the pipeline to catch accidental leaks:
- **gitleaks** -- fast, regex-based scanner
- **truffleHog** -- entropy-based detection
- **GitHub secret scanning** -- built-in for public repos

---

## Environment Promotion

Standard promotion flow: **dev -> staging -> production**.

### Strategy

```
feature branch  -->  dev (auto-deploy on merge)
                       |
                       v
                    staging (auto-deploy from main, or manual trigger)
                       |
                       v
                    production (manual approval gate)
```

### Implementation

```yaml
# GitHub Actions -- environment with approval
deploy-production:
  runs-on: ubuntu-latest
  needs: [deploy-staging]
  environment:
    name: production
    url: https://app.example.com
  steps:
    - name: Deploy
      run: ./deploy.sh production
```

### Best Practices

- Use the same artifact across all environments (build once, deploy many).
- Environment-specific config via environment variables, not rebuilds.
- Require manual approval for production deployments.
- Run smoke tests automatically after each deployment.
- Implement automatic rollback on health check failure.

---

## Monorepo Pipelines

### Path Filtering

Only run jobs when relevant files change:

```yaml
# GitHub Actions
on:
  push:
    paths:
      - 'services/api/**'
      - 'libs/shared/**'
```

### Monorepo Tools

| Tool      | Ecosystem   | Key Feature                     |
|-----------|-------------|---------------------------------|
| Turborepo | Node.js     | Remote caching, task graph      |
| Nx        | Multi-lang  | Affected detection, task graph  |
| Bazel     | Multi-lang  | Hermetic builds, remote cache   |
| Pants     | Python / Go | Fine-grained dependency graph   |

### Tips

- Define a dependency graph so changes in shared libs trigger downstream jobs.
- Cache at the package/service level, not the repo level.
- Use `--affected` or equivalent to skip unchanged packages.

---

## Pipeline Optimization

### Parallelism

- Run independent stages concurrently (lint, test, security scan).
- Split large test suites across parallel runners.

```yaml
# GitHub Actions -- parallel jobs
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]
  test:
    runs-on: ubuntu-latest
    steps: [...]
  security:
    runs-on: ubuntu-latest
    steps: [...]
  build:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    steps: [...]
```

### Fail Fast

- Put fast checks (lint, type check) before slow ones (integration tests).
- Use `fail-fast: true` in matrix builds for PR pipelines.

### Conditional Execution

- Skip heavy jobs for documentation-only changes.
- Run full test suites only on main branch; run subset on PRs.

```yaml
# Skip CI for docs-only changes
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Resource Sizing

- Use smaller runners for lint/format jobs.
- Use larger runners (or self-hosted) for build and integration tests.
- Set reasonable timeouts to avoid runaway jobs.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

---

## Pipeline Anti-Patterns

| Anti-Pattern                  | Why It Hurts                                    | Fix                                    |
|-------------------------------|------------------------------------------------|----------------------------------------|
| No caching                   | Slow builds, wasted compute                     | Cache dependencies and layers          |
| Secrets in code              | Security breach risk                            | Use secrets manager                    |
| No timeouts                  | Runaway jobs burn resources                      | Set `timeout-minutes` on every job     |
| Deploying untested code      | Bugs reach production                            | Gate deploys behind test/lint jobs     |
| Single monolithic pipeline   | Slow feedback, hard to debug                     | Split into parallel stages             |
| Manual deployments           | Inconsistent, error-prone                        | Automate with environment approvals    |
| Ignoring flaky tests         | Erodes trust in pipeline                         | Quarantine and fix flaky tests         |
