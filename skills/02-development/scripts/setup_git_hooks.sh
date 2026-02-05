#!/usr/bin/env bash
# =============================================================================
# setup_git_hooks.sh
# Installs pre-commit hooks for lint, format, secrets detection, and commit
# message validation. Detects project type (Node.js or Python) automatically.
#
# Usage:
#   bash setup_git_hooks.sh           # Run from inside a git repository
#   bash setup_git_hooks.sh --help    # Show help
#
# Features:
#   - Idempotent: safe to run multiple times
#   - Auto-detects Node.js (package.json) or Python (pyproject.toml)
#   - Installs pre-commit hook: lint, format, secrets scan
#   - Installs commit-msg hook: conventional commit validation
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Usage: bash setup_git_hooks.sh

Run this script from the root of a git repository to install pre-commit
and commit-msg hooks.

Hooks installed:
  pre-commit:
    - Lint check (eslint for Node, ruff for Python)
    - Format check (prettier for Node, ruff format for Python)
    - Secrets detection (scans staged files for common secret patterns)

  commit-msg:
    - Validates commit messages follow Conventional Commits format
    - Required format: type(scope): description
    - Valid types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert

Options:
  --help, -h    Show this help message

Notes:
  - Detects project type from package.json (Node) or pyproject.toml (Python)
  - Idempotent: existing hooks are backed up before overwriting
  - Hooks are installed to .git/hooks/ (local to the repository)
HELP
  exit 0
fi

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

# Must be inside a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  error "Not inside a git repository. Run 'git init' first."
  exit 1
fi

# Locate git hooks directory
GIT_DIR=$(git rev-parse --git-dir)
HOOKS_DIR="${GIT_DIR}/hooks"
mkdir -p "$HOOKS_DIR"

# ---------------------------------------------------------------------------
# Detect project type
# ---------------------------------------------------------------------------
PROJECT_TYPE="unknown"
if [[ -f package.json ]]; then
  PROJECT_TYPE="node"
  info "Detected Node.js project (package.json found)."
elif [[ -f pyproject.toml ]]; then
  PROJECT_TYPE="python"
  info "Detected Python project (pyproject.toml found)."
elif [[ -f go.mod ]]; then
  PROJECT_TYPE="go"
  info "Detected Go project (go.mod found)."
else
  warn "Could not detect project type. Installing generic hooks."
fi

# ---------------------------------------------------------------------------
# Helper: back up existing hook
# ---------------------------------------------------------------------------
backup_hook() {
  local hook_path="$1"
  if [[ -f "$hook_path" ]]; then
    local backup="${hook_path}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$hook_path" "$backup"
    warn "Backed up existing hook to: $backup"
  fi
}

# ---------------------------------------------------------------------------
# Build lint and format commands based on project type
# ---------------------------------------------------------------------------
generate_lint_commands() {
  case "$PROJECT_TYPE" in
    node)
      cat <<'NODE_LINT'
# --- Lint Check ---
echo "[pre-commit] Running lint check..."
if command -v npx &>/dev/null && [ -f package.json ]; then
  # Check if eslint is available
  if npx --no-install eslint --version &>/dev/null 2>&1; then
    STAGED_JS=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(ts|tsx|js|jsx)$' || true)
    if [ -n "$STAGED_JS" ]; then
      echo "$STAGED_JS" | xargs npx --no-install eslint --max-warnings 0
      if [ $? -ne 0 ]; then
        echo "[pre-commit] Lint errors found. Fix them before committing."
        exit 1
      fi
    fi
  else
    echo "[pre-commit] eslint not installed, skipping lint check."
  fi
fi
NODE_LINT
      ;;
    python)
      cat <<'PYTHON_LINT'
# --- Lint Check ---
echo "[pre-commit] Running lint check..."
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
if [ -n "$STAGED_PY" ]; then
  if command -v ruff &>/dev/null; then
    echo "$STAGED_PY" | xargs ruff check
    if [ $? -ne 0 ]; then
      echo "[pre-commit] Lint errors found. Fix them before committing."
      exit 1
    fi
  elif command -v flake8 &>/dev/null; then
    echo "$STAGED_PY" | xargs flake8
    if [ $? -ne 0 ]; then
      echo "[pre-commit] Lint errors found. Fix them before committing."
      exit 1
    fi
  else
    echo "[pre-commit] No Python linter found (ruff or flake8). Skipping lint."
  fi
fi
PYTHON_LINT
      ;;
    go)
      cat <<'GO_LINT'
# --- Lint Check ---
echo "[pre-commit] Running lint check..."
STAGED_GO=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.go$' || true)
if [ -n "$STAGED_GO" ]; then
  if command -v golangci-lint &>/dev/null; then
    golangci-lint run ./...
    if [ $? -ne 0 ]; then
      echo "[pre-commit] Lint errors found. Fix them before committing."
      exit 1
    fi
  else
    echo "[pre-commit] golangci-lint not installed, running go vet instead."
    go vet ./...
    if [ $? -ne 0 ]; then
      echo "[pre-commit] go vet found issues. Fix them before committing."
      exit 1
    fi
  fi
fi
GO_LINT
      ;;
    *)
      cat <<'GENERIC_LINT'
# --- Lint Check ---
echo "[pre-commit] No project-specific linter configured. Skipping lint."
GENERIC_LINT
      ;;
  esac
}

generate_format_commands() {
  case "$PROJECT_TYPE" in
    node)
      cat <<'NODE_FMT'
# --- Format Check ---
echo "[pre-commit] Running format check..."
if command -v npx &>/dev/null && [ -f package.json ]; then
  if npx --no-install prettier --version &>/dev/null 2>&1; then
    STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(ts|tsx|js|jsx|json|css|md)$' || true)
    if [ -n "$STAGED_FILES" ]; then
      echo "$STAGED_FILES" | xargs npx --no-install prettier --check
      if [ $? -ne 0 ]; then
        echo "[pre-commit] Formatting issues found. Run 'npx prettier --write' to fix."
        exit 1
      fi
    fi
  else
    echo "[pre-commit] prettier not installed, skipping format check."
  fi
fi
NODE_FMT
      ;;
    python)
      cat <<'PYTHON_FMT'
# --- Format Check ---
echo "[pre-commit] Running format check..."
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
if [ -n "$STAGED_PY" ]; then
  if command -v ruff &>/dev/null; then
    echo "$STAGED_PY" | xargs ruff format --check
    if [ $? -ne 0 ]; then
      echo "[pre-commit] Formatting issues found. Run 'ruff format' to fix."
      exit 1
    fi
  elif command -v black &>/dev/null; then
    echo "$STAGED_PY" | xargs black --check
    if [ $? -ne 0 ]; then
      echo "[pre-commit] Formatting issues found. Run 'black' to fix."
      exit 1
    fi
  else
    echo "[pre-commit] No Python formatter found (ruff or black). Skipping format check."
  fi
fi
PYTHON_FMT
      ;;
    go)
      cat <<'GO_FMT'
# --- Format Check ---
echo "[pre-commit] Running format check..."
STAGED_GO=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.go$' || true)
if [ -n "$STAGED_GO" ]; then
  UNFORMATTED=$(gofmt -l $STAGED_GO 2>/dev/null || true)
  if [ -n "$UNFORMATTED" ]; then
    echo "[pre-commit] The following files need formatting:"
    echo "$UNFORMATTED"
    echo "[pre-commit] Run 'gofmt -w' on the above files."
    exit 1
  fi
fi
GO_FMT
      ;;
    *)
      cat <<'GENERIC_FMT'
# --- Format Check ---
echo "[pre-commit] No project-specific formatter configured. Skipping format check."
GENERIC_FMT
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Install pre-commit hook
# ---------------------------------------------------------------------------
PRE_COMMIT_HOOK="${HOOKS_DIR}/pre-commit"
backup_hook "$PRE_COMMIT_HOOK"

cat > "$PRE_COMMIT_HOOK" <<'HOOK_HEADER'
#!/usr/bin/env bash
# =============================================================================
# pre-commit hook
# Installed by setup_git_hooks.sh
# Checks: lint, format, secrets detection
# =============================================================================

set -euo pipefail

HOOK_HEADER

# Append lint commands
generate_lint_commands >> "$PRE_COMMIT_HOOK"

echo "" >> "$PRE_COMMIT_HOOK"

# Append format commands
generate_format_commands >> "$PRE_COMMIT_HOOK"

# Append secrets detection (universal)
cat >> "$PRE_COMMIT_HOOK" <<'SECRETS_SCAN'

# --- Secrets Detection ---
echo "[pre-commit] Scanning for potential secrets..."
STAGED_ALL=$(git diff --cached --name-only --diff-filter=ACMR || true)

if [ -n "$STAGED_ALL" ]; then
  # Patterns that commonly indicate leaked secrets
  SECRET_PATTERNS=(
    'AKIA[0-9A-Z]{16}'                         # AWS Access Key ID
    'AIza[0-9A-Za-z_-]{35}'                     # Google API Key
    'sk-[0-9a-zA-Z]{20,}'                       # OpenAI / Stripe secret key
    'ghp_[0-9a-zA-Z]{36}'                       # GitHub personal access token
    'gho_[0-9a-zA-Z]{36}'                       # GitHub OAuth token
    'password\s*[:=]\s*["\x27][^"\x27]{4,}'     # password = "..." or password: "..."
    'secret\s*[:=]\s*["\x27][^"\x27]{4,}'       # secret = "..." or secret: "..."
    'api[_-]?key\s*[:=]\s*["\x27][^"\x27]{4,}'  # api_key = "..."
    'token\s*[:=]\s*["\x27][^"\x27]{4,}'        # token = "..."
  )

  FOUND_SECRETS=0
  for pattern in "${SECRET_PATTERNS[@]}"; do
    MATCHES=$(echo "$STAGED_ALL" | xargs grep -lEn "$pattern" 2>/dev/null || true)
    if [ -n "$MATCHES" ]; then
      if [ "$FOUND_SECRETS" -eq 0 ]; then
        echo "[pre-commit] WARNING: Potential secrets detected in staged files:"
      fi
      echo "  Pattern: $pattern"
      echo "  Files: $MATCHES"
      FOUND_SECRETS=1
    fi
  done

  if [ "$FOUND_SECRETS" -eq 1 ]; then
    echo ""
    echo "[pre-commit] Potential secrets found. Review the files above."
    echo "[pre-commit] If these are false positives, commit with --no-verify (use with caution)."
    exit 1
  fi
fi

echo "[pre-commit] All checks passed."
SECRETS_SCAN

chmod +x "$PRE_COMMIT_HOOK"
success "Installed pre-commit hook: $PRE_COMMIT_HOOK"

# ---------------------------------------------------------------------------
# Install commit-msg hook (Conventional Commits validation)
# ---------------------------------------------------------------------------
COMMIT_MSG_HOOK="${HOOKS_DIR}/commit-msg"
backup_hook "$COMMIT_MSG_HOOK"

cat > "$COMMIT_MSG_HOOK" <<'COMMIT_MSG'
#!/usr/bin/env bash
# =============================================================================
# commit-msg hook
# Installed by setup_git_hooks.sh
# Validates that commit messages follow Conventional Commits format.
#
# Format: type(scope): description
#         type: description
#
# Valid types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
# =============================================================================

set -euo pipefail

COMMIT_MSG_FILE="$1"
COMMIT_MSG_CONTENT=$(head -1 "$COMMIT_MSG_FILE")

# Allow merge commits and revert commits generated by git
if echo "$COMMIT_MSG_CONTENT" | grep -qE "^Merge (branch|pull request|remote)"; then
  exit 0
fi
if echo "$COMMIT_MSG_CONTENT" | grep -qE "^Revert \""; then
  exit 0
fi

# Conventional Commits regex
# Matches: type(scope): description  OR  type: description  OR  type!: description
PATTERN='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([a-zA-Z0-9._-]+\))?!?: .{1,}'

if ! echo "$COMMIT_MSG_CONTENT" | grep -qE "$PATTERN"; then
  echo ""
  echo "ERROR: Invalid commit message format."
  echo ""
  echo "  Your message:  $COMMIT_MSG_CONTENT"
  echo ""
  echo "  Expected format:"
  echo "    type(scope): description"
  echo "    type: description"
  echo ""
  echo "  Valid types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
  echo ""
  echo "  Examples:"
  echo "    feat(auth): add OAuth2 login flow"
  echo "    fix: resolve null pointer in user service"
  echo "    docs(readme): update installation instructions"
  echo ""
  exit 1
fi

# Check subject line length (max 72 characters is conventional)
SUBJECT_LENGTH=${#COMMIT_MSG_CONTENT}
if [ "$SUBJECT_LENGTH" -gt 72 ]; then
  echo ""
  echo "WARNING: Commit subject is $SUBJECT_LENGTH characters (recommended max: 72)."
  echo "  Consider shortening: $COMMIT_MSG_CONTENT"
  echo ""
  # Warning only, do not block the commit
fi

exit 0
COMMIT_MSG

chmod +x "$COMMIT_MSG_HOOK"
success "Installed commit-msg hook: $COMMIT_MSG_HOOK"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
info "========================================="
info " Git hooks installed successfully!"
info " Project type: ${PROJECT_TYPE}"
info ""
info " Hooks:"
info "   pre-commit  — lint, format, secrets scan"
info "   commit-msg  — conventional commits validation"
info ""
info " To bypass hooks (use sparingly):"
info "   git commit --no-verify"
info "========================================="
