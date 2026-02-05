#!/usr/bin/env bash
# =============================================================================
# init_project.sh
# Scaffolds a new project with standard directory structure, .gitignore,
# .editorconfig, and README skeleton based on the project type.
#
# Usage:
#   bash init_project.sh --name "my-project" --type node|python|go
#   bash init_project.sh --help
#
# Supported types:
#   node    - Node.js / TypeScript project
#   python  - Python project (pyproject.toml based)
#   go      - Go module project
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
  cat <<'USAGE'
Usage: bash init_project.sh --name <project-name> --type <node|python|go>

Options:
  --name, -n    Project name (required). Used as directory name.
  --type, -t    Project type: node, python, or go (required).
  --help, -h    Show this help message.

Examples:
  bash init_project.sh --name "my-api" --type node
  bash init_project.sh -n "data-pipeline" -t python
  bash init_project.sh -n "microservice" -t go
USAGE
  exit 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
PROJECT_NAME=""
PROJECT_TYPE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name|-n)   PROJECT_NAME="$2"; shift 2 ;;
    --type|-t)   PROJECT_TYPE="$2"; shift 2 ;;
    --help|-h)   usage ;;
    *)           error "Unknown argument: $1"; usage ;;
  esac
done

# Validate required arguments
if [[ -z "$PROJECT_NAME" ]]; then
  error "Missing required argument: --name"
  usage
fi

if [[ -z "$PROJECT_TYPE" ]]; then
  error "Missing required argument: --type"
  usage
fi

# Validate project type
case "$PROJECT_TYPE" in
  node|python|go) ;;
  *) error "Invalid project type: '$PROJECT_TYPE'. Must be node, python, or go."; exit 1 ;;
esac

# ---------------------------------------------------------------------------
# Create project root
# ---------------------------------------------------------------------------
if [[ -d "$PROJECT_NAME" ]]; then
  warn "Directory '$PROJECT_NAME' already exists. Scaffolding into existing directory."
else
  mkdir -p "$PROJECT_NAME"
  success "Created project directory: $PROJECT_NAME"
fi

cd "$PROJECT_NAME"

# ---------------------------------------------------------------------------
# .editorconfig (shared across all project types)
# ---------------------------------------------------------------------------
if [[ ! -f .editorconfig ]]; then
  cat > .editorconfig <<'EDITORCONFIG'
# EditorConfig — consistent coding styles across editors
# https://editorconfig.org

root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
EDITORCONFIG
  success "Created .editorconfig"
else
  warn ".editorconfig already exists, skipping."
fi

# ---------------------------------------------------------------------------
# Type-specific scaffolding
# ---------------------------------------------------------------------------

scaffold_node() {
  # Directory structure
  mkdir -p src tests docs .github/workflows

  # .gitignore
  if [[ ! -f .gitignore ]]; then
    cat > .gitignore <<'GITIGNORE'
# Dependencies
node_modules/

# Build output
dist/
build/
*.js.map

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Test / Coverage
coverage/
.nyc_output/

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Misc
*.tgz
.cache/
GITIGNORE
    success "Created .gitignore (node)"
  fi

  # package.json skeleton
  if [[ ! -f package.json ]]; then
    cat > package.json <<PACKAGE
{
  "name": "${PROJECT_NAME}",
  "version": "0.1.0",
  "description": "",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts",
    "test": "jest",
    "lint": "eslint src/ --ext .ts,.js",
    "format": "prettier --write 'src/**/*.{ts,js,json}'"
  },
  "keywords": [],
  "license": "MIT"
}
PACKAGE
    success "Created package.json"
  fi

  # tsconfig.json skeleton
  if [[ ! -f tsconfig.json ]]; then
    cat > tsconfig.json <<'TSCONFIG'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
TSCONFIG
    success "Created tsconfig.json"
  fi

  # Placeholder source file
  if [[ ! -f src/index.ts ]]; then
    cat > src/index.ts <<'SRC'
/**
 * Application entry point.
 */

export function main(): void {
  console.log("Hello from ${PROJECT_NAME}");
}

main();
SRC
    success "Created src/index.ts"
  fi

  # Update .editorconfig indent for node (already 2-space, which is standard)
  info "Node project uses 2-space indentation (already set in .editorconfig)."
}

scaffold_python() {
  # Directory structure — src layout
  local pkg_name="${PROJECT_NAME//-/_}"
  mkdir -p "src/${pkg_name}" tests docs

  # .gitignore
  if [[ ! -f .gitignore ]]; then
    cat > .gitignore <<'GITIGNORE'
# Byte-compiled / optimized
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/
env/

# Distribution / packaging
dist/
build/
*.egg-info/
*.egg

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Test / Coverage
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Jupyter
.ipynb_checkpoints/

# Logs
*.log
GITIGNORE
    success "Created .gitignore (python)"
  fi

  # pyproject.toml
  if [[ ! -f pyproject.toml ]]; then
    cat > pyproject.toml <<PYPROJECT
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "${PROJECT_NAME}"
version = "0.1.0"
description = ""
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.10"
strict = true
PYPROJECT
    success "Created pyproject.toml"
  fi

  # Package init
  if [[ ! -f "src/${pkg_name}/__init__.py" ]]; then
    cat > "src/${pkg_name}/__init__.py" <<INIT
"""${PROJECT_NAME} — top-level package."""

__version__ = "0.1.0"
INIT
    success "Created src/${pkg_name}/__init__.py"
  fi

  # Main module
  if [[ ! -f "src/${pkg_name}/main.py" ]]; then
    cat > "src/${pkg_name}/main.py" <<'MAIN'
"""Application entry point."""


def main() -> None:
    """Run the application."""
    print("Hello from the application")


if __name__ == "__main__":
    main()
MAIN
    success "Created src/${pkg_name}/main.py"
  fi

  # Tests init
  if [[ ! -f tests/__init__.py ]]; then
    touch tests/__init__.py
  fi

  # Update .editorconfig for python 4-space indent
  if [[ -f .editorconfig ]]; then
    cat >> .editorconfig <<'PYEDITOR'

[*.py]
indent_size = 4
PYEDITOR
    info "Added Python 4-space indent rule to .editorconfig."
  fi
}

scaffold_go() {
  # Directory structure
  mkdir -p cmd internal pkg docs

  # .gitignore
  if [[ ! -f .gitignore ]]; then
    cat > .gitignore <<'GITIGNORE'
# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib
/bin/

# Test binary
*.test

# Coverage
coverage.out
coverage.html

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Vendor (uncomment if you commit vendor/)
# vendor/

# Go workspace
go.work
GITIGNORE
    success "Created .gitignore (go)"
  fi

  # go.mod
  if [[ ! -f go.mod ]]; then
    cat > go.mod <<GOMOD
module github.com/yourorg/${PROJECT_NAME}

go 1.21
GOMOD
    success "Created go.mod"
  fi

  # main.go
  if [[ ! -f cmd/main.go ]]; then
    cat > cmd/main.go <<'GOMAIN'
package main

import "fmt"

func main() {
	fmt.Println("Hello from the application")
}
GOMAIN
    success "Created cmd/main.go"
  fi

  # Makefile
  if [[ ! -f Makefile ]]; then
    cat > Makefile <<MAKEFILE
.PHONY: build run test lint clean

APP_NAME := ${PROJECT_NAME}

build:
	go build -o bin/\$(APP_NAME) ./cmd/...

run: build
	./bin/\$(APP_NAME)

test:
	go test ./... -v -cover

lint:
	golangci-lint run ./...

clean:
	rm -rf bin/
MAKEFILE
    success "Created Makefile"
  fi

  # Update .editorconfig for go tab indent
  if [[ -f .editorconfig ]]; then
    cat >> .editorconfig <<'GOEDITOR'

[*.go]
indent_style = tab
indent_size = 4
GOEDITOR
    info "Added Go tab-indent rule to .editorconfig."
  fi
}

# ---------------------------------------------------------------------------
# Run type-specific scaffolding
# ---------------------------------------------------------------------------
info "Scaffolding $PROJECT_TYPE project: $PROJECT_NAME"
echo ""

case "$PROJECT_TYPE" in
  node)   scaffold_node   ;;
  python) scaffold_python ;;
  go)     scaffold_go     ;;
esac

# ---------------------------------------------------------------------------
# README.md skeleton
# ---------------------------------------------------------------------------
if [[ ! -f README.md ]]; then
  cat > README.md <<README
# ${PROJECT_NAME}

> One-line description of the project.

## Getting Started

### Prerequisites
$(case "$PROJECT_TYPE" in
  node)   echo "- Node.js >= 18" ;;
  python) echo "- Python >= 3.10" ;;
  go)     echo "- Go >= 1.21" ;;
esac)

### Installation
\`\`\`bash
$(case "$PROJECT_TYPE" in
  node)   echo "npm install" ;;
  python) echo "python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'" ;;
  go)     echo "go mod download" ;;
esac)
\`\`\`

### Running
\`\`\`bash
$(case "$PROJECT_TYPE" in
  node)   echo "npm run dev" ;;
  python) echo "python -m src.${PROJECT_NAME//-/_}.main" ;;
  go)     echo "make run" ;;
esac)
\`\`\`

### Testing
\`\`\`bash
$(case "$PROJECT_TYPE" in
  node)   echo "npm test" ;;
  python) echo "pytest" ;;
  go)     echo "make test" ;;
esac)
\`\`\`

## Project Structure
\`\`\`
$(case "$PROJECT_TYPE" in
  node)
    echo "${PROJECT_NAME}/"
    echo "  src/           # Application source"
    echo "  tests/         # Test files"
    echo "  docs/          # Documentation"
    echo "  package.json   # Dependencies and scripts"
    echo "  tsconfig.json  # TypeScript configuration"
    ;;
  python)
    echo "${PROJECT_NAME}/"
    echo "  src/           # Application source"
    echo "  tests/         # Test files"
    echo "  docs/          # Documentation"
    echo "  pyproject.toml # Project metadata and dependencies"
    ;;
  go)
    echo "${PROJECT_NAME}/"
    echo "  cmd/           # Application entry points"
    echo "  internal/      # Private application code"
    echo "  pkg/           # Public library code"
    echo "  docs/          # Documentation"
    echo "  go.mod         # Module definition"
    ;;
esac)
\`\`\`

## Contributing
See the project's development guidelines for branching strategy, commit conventions, and code review process.

## License
MIT
README
  success "Created README.md"
else
  warn "README.md already exists, skipping."
fi

# ---------------------------------------------------------------------------
# Initialize git repository (if not already initialized)
# ---------------------------------------------------------------------------
if [[ ! -d .git ]]; then
  git init -q
  success "Initialized git repository."
else
  warn "Git repository already initialized."
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
info "========================================="
info " Project scaffolded successfully!"
info " Name: ${PROJECT_NAME}"
info " Type: ${PROJECT_TYPE}"
info " Path: $(pwd)"
info "========================================="
echo ""
info "Next steps:"
info "  1. cd ${PROJECT_NAME}"
info "  2. Set up git hooks:  bash ../skills/02-development/scripts/setup_git_hooks.sh"
info "  3. Start developing!"
