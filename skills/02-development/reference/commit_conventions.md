# Conventional Commits Specification

## Overview

Conventional Commits is a specification for writing structured, human- and machine-readable commit messages. It provides a shared vocabulary that enables automated tooling for changelogs, versioning, and release management.

Specification: [conventionalcommits.org](https://www.conventionalcommits.org/)

---

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Structure Breakdown

| Part | Required | Description |
|------|----------|-------------|
| `type` | Yes | Category of change (see types below) |
| `scope` | No | Module, component, or area affected |
| `description` | Yes | Short summary in imperative mood |
| `body` | No | Detailed explanation of what and why |
| `footer` | No | Breaking changes, issue references |

### Rules

1. **Type** must be one of the allowed types (see below).
2. **Scope** is optional, enclosed in parentheses: `type(scope): ...`
3. **Description** must immediately follow the colon and space after type/scope.
4. **Description** uses imperative mood ("add" not "added" or "adds").
5. **Description** does not end with a period.
6. **Description** starts with lowercase.
7. **Body** is separated from description by a blank line.
8. **Footer** is separated from body by a blank line.
9. **Breaking changes** are indicated by `!` after type/scope or `BREAKING CHANGE:` in footer.

---

## Types

| Type | Description | SemVer Impact |
|------|-------------|---------------|
| `feat` | A new feature | MINOR bump |
| `fix` | A bug fix | PATCH bump |
| `docs` | Documentation only | None |
| `style` | Code style (formatting, semicolons, etc.) | None |
| `refactor` | Code change that neither fixes a bug nor adds a feature | None |
| `test` | Adding or correcting tests | None |
| `chore` | Maintenance tasks (deps, build config, tooling) | None |
| `perf` | Performance improvement | PATCH bump |
| `ci` | CI/CD configuration changes | None |
| `build` | Build system or external dependency changes | None |
| `revert` | Reverts a previous commit | Varies |

### When to use each

- **feat** -- You are adding behavior the user can observe. A new endpoint, UI component, CLI flag.
- **fix** -- Something was broken and you made it work correctly. Includes edge case fixes.
- **docs** -- README updates, JSDoc/docstring changes, comment improvements. No code behavior change.
- **style** -- Whitespace, formatting, missing semicolons. No logic change.
- **refactor** -- Restructuring code without changing external behavior. Renaming, extracting functions.
- **test** -- Adding missing tests or fixing existing tests. No production code change.
- **chore** -- Updating dependencies, configuring tools, modifying `.gitignore`. Housekeeping.
- **perf** -- Optimizing an algorithm, reducing bundle size, caching. Measurable improvement.
- **ci** -- Changes to CI config files and scripts (GitHub Actions, Jenkins, etc.).
- **build** -- Changes to the build process (webpack, tsconfig, Dockerfile).
- **revert** -- Undoing a previous commit. Reference the reverted commit in the body.

---

## Scope

The scope identifies the area of the codebase affected. It is project-specific and optional.

### Common scope examples

```
feat(auth): add OAuth2 login flow
fix(api): handle timeout in user service
docs(readme): update installation steps
refactor(payments): extract billing calculator
test(auth): add unit tests for token refresh
chore(deps): bump express from 4.18 to 4.19
ci(github): add caching to Node.js workflow
```

### Scope conventions for this project

Define your scopes based on your project structure. Examples:
- Module names: `auth`, `payments`, `users`, `api`
- Layer names: `db`, `ui`, `middleware`, `config`
- Tool names: `eslint`, `docker`, `terraform`

Keep scopes lowercase, hyphenated, and consistent.

---

## Breaking Changes

Breaking changes indicate that the public API has changed in an incompatible way. They trigger a MAJOR version bump.

### Method 1: Exclamation mark
```
feat(api)!: change authentication to use JWT instead of sessions
```

### Method 2: Footer
```
feat(api): change authentication to use JWT instead of sessions

BREAKING CHANGE: The /auth/login endpoint now returns a JWT token
instead of setting a session cookie. All clients must update their
authentication handling.
```

Both methods can be combined. The footer should describe what changed and what consumers need to do.

---

## Examples

### Good Commits

```
feat(auth): add Google OAuth2 login

Implement Google OAuth2 authentication flow using passport-google-oauth20.
Users can now sign in with their Google accounts.

Closes #142
```

```
fix: prevent race condition in order processing

The order service was processing duplicate events when two webhooks
arrived within the same millisecond. Added idempotency key check
before processing.

Fixes #298
```

```
docs: add API authentication guide to README
```

```
refactor(db): extract connection pooling into shared module

Move database connection pool configuration from individual services
into a shared module to reduce duplication and ensure consistent
pool settings across services.
```

```
chore(deps): update TypeScript from 5.2 to 5.3

No breaking changes. Enables new decorators syntax.
```

```
perf(search): add Redis caching for frequent queries

Cache the top 100 search queries with a 5-minute TTL.
Reduces average search latency from 450ms to 12ms for cached queries.
```

```
feat(api)!: require API key for all endpoints

BREAKING CHANGE: All API endpoints now require an X-API-Key header.
Unauthenticated requests will receive a 401 response. See the
migration guide at docs/migration-v3.md.
```

```
revert: feat(auth): add Google OAuth2 login

This reverts commit abc1234. The OAuth integration caused login
failures for users with non-Gmail Google accounts.
```

### Bad Commits (and how to fix them)

| Bad | Problem | Better |
|-----|---------|--------|
| `fixed stuff` | No type, vague description | `fix(auth): resolve null pointer on login` |
| `WIP` | No information at all | `feat(cart): add quantity validation (wip)` |
| `update` | No type, no description of what changed | `chore(deps): update lodash to 4.17.21` |
| `Fix bug #123` | No type prefix, capitalized | `fix: handle empty response from payment API` |
| `feat: Added new feature for users to be able to reset their passwords.` | Past tense, too long, ends with period | `feat(auth): add password reset flow` |
| `refactor + fix + test` | Multiple concerns in one commit | Split into three separate commits |
| `JIRA-456` | Ticket number is not a description | `feat(reports): add CSV export for monthly reports` |

---

## Multi-line Commit Messages

For significant changes, use the body to explain context:

```
type(scope): short description (max ~50 chars ideal)
                                                    <-- blank line
Longer explanation of what changed and why. Wrap at 72 characters.
Explain the problem this commit solves, not just what the code does.

- Bullet points are fine
- Use them for listing multiple changes

Reference issues at the bottom.

Closes #123
Refs #456
```

### Subject line guidelines
- Limit to 72 characters (50 is ideal)
- Use imperative mood: "add" not "added" or "adds"
- Do not end with a period
- Capitalize the first letter of the description (after the colon)... actually, lowercase is the convention for conventional commits

### Body guidelines
- Wrap at 72 characters
- Explain *what* and *why*, not *how* (the code shows how)
- Use bullet points for multiple items

---

## Automation Benefits

Conventional commits enable powerful automation:

### 1. Automated Changelogs

Tools like `conventional-changelog`, `release-please`, or `semantic-release` can parse commit history and generate changelogs:

```markdown
## [1.3.0] - 2026-02-05

### Features
- **auth:** add Google OAuth2 login (#142)
- **reports:** add CSV export for monthly reports (#189)

### Bug Fixes
- **api:** handle timeout in user service (#156)
- prevent race condition in order processing (#298)

### Performance
- **search:** add Redis caching for frequent queries (#201)
```

### 2. Automated Versioning

Based on commit types since the last release:
- Any `feat` commit --> bump MINOR version
- Any `fix` or `perf` commit --> bump PATCH version
- Any `BREAKING CHANGE` --> bump MAJOR version
- `docs`, `style`, `refactor`, `test`, `chore`, `ci` --> no version bump

### 3. Automated Release Notes

GitHub Releases and similar tools can generate rich release notes from structured commits, grouping changes by type and linking to PRs.

### 4. Commit Linting

Enforce the format in CI or git hooks using tools:
- **commitlint** (Node.js): `npx commitlint --edit $1`
- **gitlint** (Python): `gitlint --commit $1`
- **Custom hook**: The `setup_git_hooks.sh` script in this project installs a commit-msg hook for validation.

### 5. Filtered Git Log

Conventional commits make it easy to search history:
```bash
# All features
git log --oneline --grep="^feat"

# All fixes for the auth module
git log --oneline --grep="^fix(auth)"

# All breaking changes
git log --oneline --grep="BREAKING CHANGE"
```

---

## Quick Reference Card

```
feat(scope): add something new          --> MINOR bump
fix(scope): correct a bug               --> PATCH bump
docs(scope): update documentation       --> no bump
style(scope): formatting only           --> no bump
refactor(scope): restructure code       --> no bump
test(scope): add or fix tests           --> no bump
chore(scope): maintenance tasks         --> no bump
perf(scope): improve performance        --> PATCH bump
ci(scope): CI/CD changes                --> no bump
build(scope): build system changes      --> no bump
revert: undo a previous commit          --> varies

Breaking change: add ! after scope      --> MAJOR bump
  feat(api)!: rename endpoints
```
