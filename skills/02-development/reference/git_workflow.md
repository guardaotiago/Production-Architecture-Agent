# Git Branching Strategy Guide

## Overview

A branching strategy defines how a team uses branches to develop features, fix bugs, and ship releases. The right strategy depends on team size, release cadence, and deployment model.

This guide covers the three most common strategies, when to use each, and the supporting conventions that make them work.

---

## Strategy Comparison

### Git Flow

A structured model with long-lived `main` and `develop` branches plus short-lived feature, release, and hotfix branches.

```
main ─────●───────────────●───────────●──── (tagged releases)
           \             / \         /
develop ────●───●───●───●───●───●───●────── (integration)
             \     /         \   /
feature/      ●───●           ●─●
```

**Branch types:**
| Branch | Purpose | Created from | Merges into |
|--------|---------|-------------|-------------|
| `main` | Production-ready code | -- | -- |
| `develop` | Integration branch | `main` | `main` (via release) |
| `feature/*` | New features | `develop` | `develop` |
| `release/*` | Release preparation | `develop` | `main` + `develop` |
| `hotfix/*` | Urgent production fixes | `main` | `main` + `develop` |

**When to use:**
- Scheduled releases (not continuous deployment)
- Multiple versions supported in production
- Larger teams (5+ developers)
- Need for release candidates and stabilization

**Drawbacks:**
- Overhead from managing multiple long-lived branches
- Merge conflicts between `develop` and `main` can accumulate
- Slower feedback loop

---

### GitHub Flow

A simplified model with a single `main` branch. All work happens on short-lived feature branches merged via pull requests.

```
main ─────●───●───●───●───●───●───●──── (always deployable)
           \   /     \   /     \   /
feature/    ●─●       ●─●       ●─●
```

**Branch types:**
| Branch | Purpose | Created from | Merges into |
|--------|---------|-------------|-------------|
| `main` | Production-ready code | -- | -- |
| `feature/*` | All work (features, fixes) | `main` | `main` |

**When to use:**
- Continuous deployment or frequent releases
- Small to medium teams (1-10 developers)
- Web applications where only one version is live
- Teams that prioritize simplicity

**Drawbacks:**
- No staging branch for release preparation
- Must rely on feature flags for partially-complete work
- Less ceremony can mean less oversight

---

### Trunk-Based Development

Developers commit directly to `main` (or via very short-lived branches that live less than a day). Relies heavily on feature flags and CI.

```
main ─────●─●─●─●─●─●─●─●─●──── (continuous integration)
           \/ (short-lived, <1 day)
            ●
```

**When to use:**
- High CI/CD maturity with strong automated testing
- Experienced teams with high trust
- Microservices or small codebases
- Maximum speed and minimum process

**Drawbacks:**
- Requires excellent test coverage and CI
- Feature flags add complexity
- Risky without strong engineering discipline

---

## Recommended Strategy by Context

| Context | Recommended Strategy |
|---------|---------------------|
| Solo / hobby project | GitHub Flow |
| Startup (2-5 devs) | GitHub Flow |
| Growing team (5-15 devs) | GitHub Flow or Git Flow (light) |
| Enterprise / regulated | Git Flow |
| Platform / SaaS with CD | Trunk-Based or GitHub Flow |
| Mobile app (app store releases) | Git Flow |

---

## Branch Naming Conventions

Consistent naming makes branches discoverable and automatable.

### Format
```
<type>/<ticket>-<short-description>
```

### Types
| Prefix | Use for |
|--------|---------|
| `feature/` | New features and enhancements |
| `fix/` | Bug fixes |
| `hotfix/` | Urgent production fixes |
| `release/` | Release preparation |
| `docs/` | Documentation-only changes |
| `refactor/` | Code restructuring (no behavior change) |
| `test/` | Adding or updating tests |
| `chore/` | Maintenance tasks (deps, config) |

### Examples
```
feature/PROJ-123-user-authentication
fix/PROJ-456-null-pointer-dashboard
hotfix/PROJ-789-payment-timeout
release/v2.1.0
docs/update-api-reference
refactor/extract-payment-service
```

### Rules
- Use lowercase and hyphens (no spaces, no underscores in description)
- Include ticket ID when available
- Keep descriptions short but meaningful (3-5 words)
- Delete branches after merging

---

## Pull Request Process

### Opening a PR

1. **Push your branch** to the remote.
2. **Create a PR** with:
   - Clear title following commit conventions (e.g., `feat(auth): add OAuth2 login`)
   - Description explaining *what* changed and *why*
   - Link to the ticket or issue
   - Screenshots or recordings for UI changes
   - Testing instructions
3. **Assign reviewers** -- at least one required approval.
4. **Ensure CI passes** before requesting review.

### Reviewing a PR

Check for:
- **Correctness** -- Does it solve the stated problem?
- **Design** -- Is the approach sound? Any simpler alternatives?
- **Readability** -- Can you understand it without the author explaining?
- **Tests** -- Are there adequate tests? Do edge cases have coverage?
- **Security** -- Any new attack surfaces, leaked data, or vulnerabilities?
- **Performance** -- Any obvious bottlenecks introduced?

### PR Size Guidelines

| Lines Changed | Assessment |
|---------------|------------|
| < 100 | Excellent -- quick to review |
| 100-400 | Good -- manageable |
| 400-800 | Large -- consider splitting |
| > 800 | Too large -- must split |

Smaller PRs get reviewed faster, have fewer bugs, and are easier to revert.

---

## Merge vs Rebase

### Merge Commit (default)
```bash
git checkout main
git merge --no-ff feature/my-feature
```
- Preserves full branch history
- Creates a merge commit
- Best for: shared branches, release merges, audit trails

### Squash and Merge
```bash
# GitHub: "Squash and merge" button
```
- Combines all branch commits into one
- Clean linear history on `main`
- Best for: feature branches with messy WIP commits

### Rebase
```bash
git checkout feature/my-feature
git rebase main
git checkout main
git merge --ff-only feature/my-feature
```
- Replays commits on top of `main`
- Linear history without merge commits
- Best for: personal branches, before opening a PR

### Recommendation

| Scenario | Strategy |
|----------|----------|
| Merging feature to `main` | Squash and merge |
| Updating feature from `main` | Rebase |
| Merging release to `main` | Merge commit (no fast-forward) |
| Merging hotfix | Merge commit |

**Golden rule:** Never rebase commits that have been pushed and shared with others.

---

## Release Tagging

### Semantic Versioning (SemVer)
```
vMAJOR.MINOR.PATCH
```
- **MAJOR** -- breaking changes
- **MINOR** -- new features, backward-compatible
- **PATCH** -- bug fixes, backward-compatible

### Tagging a Release
```bash
# Annotated tag (recommended)
git tag -a v1.2.0 -m "Release v1.2.0: Add payment processing"
git push origin v1.2.0

# List tags
git tag -l "v1.*"
```

### Pre-release Tags
```
v1.2.0-alpha.1
v1.2.0-beta.1
v1.2.0-rc.1
```

### Automation
Tags can trigger automated workflows:
- CI/CD pipeline builds and deploys on new tag
- Changelog generated from conventional commits since last tag
- GitHub Release created with release notes
