# Code Formatting Guide

This project uses automated code formatting tools to ensure consistent code style.

## Backend (Python)

### Installation

Install Ruff:
```bash
# Using pip
pip install ruff

# Or using pipx (recommended)
pipx install ruff

# Or using homebrew (macOS)
brew install ruff
```

### Usage

**Format code:**
```bash
cd backend
ruff format .
```

**Check formatting (without making changes):**
```bash
cd backend
ruff format --check .
```

**Lint code:**
```bash
cd backend
ruff check .
```

**Auto-fix linting issues:**
```bash
cd backend
ruff check --fix .
```

**Format and lint together:**
```bash
cd backend
ruff check --fix . && ruff format .
```

## Frontend (TypeScript/React)

### Installation

Prettier is already included in `package.json` devDependencies. Install with:
```bash
npm install
```

### Usage

**Format code:**
```bash
npm run format
```

**Check formatting (without making changes):**
```bash
npm run format:check
```

**Lint code:**
```bash
npm run lint
```

## Pre-commit Hooks (Optional)

To automatically format code before commits, you can set up pre-commit hooks:

### Backend
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: ^(client|shared)/
EOF

# Install hooks
pre-commit install
```

## CI/CD

Formatting and linting are automatically checked in CI:
- **Backend**: Ruff format check and lint check
- **Frontend**: Prettier format check and ESLint

All checks must pass before merging pull requests.

