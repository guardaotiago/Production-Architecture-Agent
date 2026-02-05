#!/usr/bin/env python3
"""Generate CI/CD pipeline configuration files.

Produces production-ready pipeline configs for GitHub Actions, GitLab CI,
or Jenkins based on the project type (node, python, go).

Usage:
    python generate_pipeline.py --platform github --type node
    python generate_pipeline.py --platform gitlab --type python --output custom/path.yml
    python generate_pipeline.py --platform jenkins --type go --dry-run
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Pipeline templates
# ---------------------------------------------------------------------------

GITHUB_NODE = textwrap.dedent("""\
    name: CI

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      ci:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            node-version: [18, 20, 22]

        steps:
          - uses: actions/checkout@v4

          - name: Use Node.js ${{ matrix.node-version }}
            uses: actions/setup-node@v4
            with:
              node-version: ${{ matrix.node-version }}
              cache: npm

          - name: Install dependencies
            run: npm ci

          - name: Lint
            run: npm run lint

          - name: Test with coverage
            run: npm test -- --coverage

          - name: Security audit
            run: npm audit --audit-level=high

          - name: Build
            run: npm run build
""")

GITHUB_PYTHON = textwrap.dedent("""\
    name: CI

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      ci:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version: ["3.10", "3.11", "3.12"]

        steps:
          - uses: actions/checkout@v4

          - name: Set up Python ${{ matrix.python-version }}
            uses: actions/setup-python@v5
            with:
              python-version: ${{ matrix.python-version }}
              cache: pip

          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install ruff pytest pytest-cov mypy bandit

          - name: Lint with ruff
            run: ruff check .

          - name: Type check with mypy
            run: mypy . --ignore-missing-imports

          - name: Test with coverage
            run: pytest --cov=. --cov-report=xml

          - name: Security scan with bandit
            run: bandit -r . -x ./tests

          - name: Build
            run: python -m build || echo "No build step configured"
""")

GITHUB_GO = textwrap.dedent("""\
    name: CI

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      ci:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            go-version: ["1.21", "1.22"]

        steps:
          - uses: actions/checkout@v4

          - name: Set up Go ${{ matrix.go-version }}
            uses: actions/setup-go@v5
            with:
              go-version: ${{ matrix.go-version }}

          - name: Install dependencies
            run: go mod download

          - name: Lint with golangci-lint
            uses: golangci/golangci-lint-action@v4
            with:
              version: latest

          - name: Test with coverage
            run: go test -v -race -coverprofile=coverage.out ./...

          - name: Security scan with govulncheck
            run: |
              go install golang.org/x/vuln/cmd/govulncheck@latest
              govulncheck ./...

          - name: Build
            run: go build -v ./...
""")

GITLAB_NODE = textwrap.dedent("""\
    stages:
      - install
      - lint
      - test
      - security
      - build

    variables:
      NODE_VERSION: "20"

    default:
      image: node:${NODE_VERSION}
      cache:
        key: ${CI_COMMIT_REF_SLUG}
        paths:
          - node_modules/

    install:
      stage: install
      script:
        - npm ci

    lint:
      stage: lint
      script:
        - npm run lint

    test:
      stage: test
      script:
        - npm test -- --coverage
      coverage: '/All files[^|]*\\|[^|]*\\s+([\\d.]+)/'
      artifacts:
        reports:
          junit: junit.xml
          coverage_report:
            coverage_format: cobertura
            path: coverage/cobertura-coverage.xml

    security:
      stage: security
      script:
        - npm audit --audit-level=high

    build:
      stage: build
      script:
        - npm run build
      artifacts:
        paths:
          - dist/
""")

GITLAB_PYTHON = textwrap.dedent("""\
    stages:
      - install
      - lint
      - test
      - security
      - build

    variables:
      PYTHON_VERSION: "3.12"

    default:
      image: python:${PYTHON_VERSION}-slim
      cache:
        key: ${CI_COMMIT_REF_SLUG}
        paths:
          - .cache/pip/

    install:
      stage: install
      script:
        - pip install --cache-dir .cache/pip -r requirements.txt
        - pip install ruff pytest pytest-cov mypy bandit

    lint:
      stage: lint
      script:
        - ruff check .

    test:
      stage: test
      script:
        - pytest --cov=. --cov-report=xml --junitxml=report.xml
      artifacts:
        reports:
          junit: report.xml
          coverage_report:
            coverage_format: cobertura
            path: coverage.xml

    security:
      stage: security
      script:
        - bandit -r . -x ./tests

    build:
      stage: build
      script:
        - python -m build || echo "No build step configured"
""")

GITLAB_GO = textwrap.dedent("""\
    stages:
      - install
      - lint
      - test
      - security
      - build

    variables:
      GO_VERSION: "1.22"

    default:
      image: golang:${GO_VERSION}
      cache:
        key: ${CI_COMMIT_REF_SLUG}
        paths:
          - /go/pkg/mod/

    install:
      stage: install
      script:
        - go mod download

    lint:
      stage: lint
      script:
        - go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
        - golangci-lint run

    test:
      stage: test
      script:
        - go test -v -race -coverprofile=coverage.out ./...
        - go tool cover -func=coverage.out

    security:
      stage: security
      script:
        - go install golang.org/x/vuln/cmd/govulncheck@latest
        - govulncheck ./...

    build:
      stage: build
      script:
        - go build -v ./...
      artifacts:
        paths:
          - bin/
""")

JENKINS_NODE = textwrap.dedent("""\
    pipeline {
        agent any

        tools {
            nodejs 'NodeJS-20'
        }

        environment {
            CI = 'true'
        }

        stages {
            stage('Install') {
                steps {
                    sh 'npm ci'
                }
            }

            stage('Lint') {
                steps {
                    sh 'npm run lint'
                }
            }

            stage('Test') {
                steps {
                    sh 'npm test -- --coverage'
                }
                post {
                    always {
                        junit 'junit.xml'
                        publishHTML(target: [
                            reportDir: 'coverage/lcov-report',
                            reportFiles: 'index.html',
                            reportName: 'Coverage Report'
                        ])
                    }
                }
            }

            stage('Security') {
                steps {
                    sh 'npm audit --audit-level=high'
                }
            }

            stage('Build') {
                steps {
                    sh 'npm run build'
                }
            }
        }

        post {
            failure {
                echo 'Pipeline failed!'
            }
            success {
                echo 'Pipeline succeeded!'
            }
        }
    }
""")

JENKINS_PYTHON = textwrap.dedent("""\
    pipeline {
        agent any

        environment {
            CI = 'true'
        }

        stages {
            stage('Install') {
                steps {
                    sh '''
                        python -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install ruff pytest pytest-cov mypy bandit
                    '''
                }
            }

            stage('Lint') {
                steps {
                    sh '''
                        . venv/bin/activate
                        ruff check .
                    '''
                }
            }

            stage('Type Check') {
                steps {
                    sh '''
                        . venv/bin/activate
                        mypy . --ignore-missing-imports
                    '''
                }
            }

            stage('Test') {
                steps {
                    sh '''
                        . venv/bin/activate
                        pytest --cov=. --cov-report=xml --junitxml=report.xml
                    '''
                }
                post {
                    always {
                        junit 'report.xml'
                    }
                }
            }

            stage('Security') {
                steps {
                    sh '''
                        . venv/bin/activate
                        bandit -r . -x ./tests
                    '''
                }
            }

            stage('Build') {
                steps {
                    sh '''
                        . venv/bin/activate
                        python -m build || echo "No build step configured"
                    '''
                }
            }
        }

        post {
            failure {
                echo 'Pipeline failed!'
            }
            success {
                echo 'Pipeline succeeded!'
            }
            always {
                cleanWs()
            }
        }
    }
""")

JENKINS_GO = textwrap.dedent("""\
    pipeline {
        agent any

        tools {
            go 'Go-1.22'
        }

        environment {
            CI = 'true'
            GOPATH = "${WORKSPACE}/go"
        }

        stages {
            stage('Install') {
                steps {
                    sh 'go mod download'
                }
            }

            stage('Lint') {
                steps {
                    sh '''
                        go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
                        golangci-lint run
                    '''
                }
            }

            stage('Test') {
                steps {
                    sh 'go test -v -race -coverprofile=coverage.out ./...'
                }
                post {
                    always {
                        sh 'go tool cover -func=coverage.out'
                    }
                }
            }

            stage('Security') {
                steps {
                    sh '''
                        go install golang.org/x/vuln/cmd/govulncheck@latest
                        govulncheck ./...
                    '''
                }
            }

            stage('Build') {
                steps {
                    sh 'go build -v ./...'
                }
            }
        }

        post {
            failure {
                echo 'Pipeline failed!'
            }
            success {
                echo 'Pipeline succeeded!'
            }
            always {
                cleanWs()
            }
        }
    }
""")

# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

TEMPLATES = {
    "github": {
        "node": GITHUB_NODE,
        "python": GITHUB_PYTHON,
        "go": GITHUB_GO,
    },
    "gitlab": {
        "node": GITLAB_NODE,
        "python": GITLAB_PYTHON,
        "go": GITLAB_GO,
    },
    "jenkins": {
        "node": JENKINS_NODE,
        "python": JENKINS_PYTHON,
        "go": JENKINS_GO,
    },
}

DEFAULT_OUTPUTS = {
    "github": ".github/workflows/ci.yml",
    "gitlab": ".gitlab-ci.yml",
    "jenkins": "Jenkinsfile",
}


def get_template(platform: str, project_type: str) -> str:
    """Retrieve the pipeline template for a given platform and project type."""
    platform_templates = TEMPLATES.get(platform)
    if platform_templates is None:
        print(f"Error: unsupported platform '{platform}'.", file=sys.stderr)
        print(f"Supported platforms: {', '.join(TEMPLATES.keys())}", file=sys.stderr)
        sys.exit(1)

    template = platform_templates.get(project_type)
    if template is None:
        print(
            f"Error: unsupported project type '{project_type}' for platform '{platform}'.",
            file=sys.stderr,
        )
        print(
            f"Supported types: {', '.join(platform_templates.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    return template


def write_pipeline(content: str, output_path: str, dry_run: bool = False) -> None:
    """Write the pipeline config to disk, or print it in dry-run mode."""
    if dry_run:
        print(f"# Dry run -- would write to: {output_path}")
        print(f"# ({len(content.splitlines())} lines)")
        print()
        print(content)
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Pipeline config written to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CI/CD pipeline configuration files.",
        epilog=(
            "Examples:\n"
            "  %(prog)s --platform github --type node\n"
            "  %(prog)s --platform gitlab --type python --output custom/ci.yml\n"
            "  %(prog)s --platform jenkins --type go --dry-run\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=["github", "gitlab", "jenkins"],
        help="CI platform to generate config for",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["node", "python", "go"],
        dest="project_type",
        help="Project type (language/runtime)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Custom output path (default: platform-standard location)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated config to stdout without writing to disk",
    )

    args = parser.parse_args()

    template = get_template(args.platform, args.project_type)
    output_path = args.output or DEFAULT_OUTPUTS[args.platform]

    write_pipeline(template, output_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
