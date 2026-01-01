# Modern Python Tooling for Auraframes

## Overview

Modernize auraframes with current Python best practices: `uv` + `ruff` + `pytest` + `mypy` + `pyproject.toml`.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package manager | uv | 10-100x faster than pip, modern standard, handles venv too |
| Linting + formatting | ruff (consolidated) | Single tool replaces black + flake8 + isort + pylint |
| Testing | pytest | Industry standard, user prefers it |
| Type checking | mypy (strict attempt) | Try strict first; relax if needed for practicality |
| Project config | pyproject.toml (full migration) | PEP 621 standard, single source of truth |
| Pre-commit | Yes | Auto-run ruff on commit, catch issues early |
| Python version | 3.10+ | Modern syntax, good library support |
| Existing issues | File GH issue, fix on separate branch | Don't block this PR with cleanup |

## Interview Insights

- User values consolidation (ruff over black+flake8) to minimize tool sprawl
- Strict typing is ideal but pragmatism wins - "make it work" if strict fails
- Core test coverage (login, frames, upload) prioritized over comprehensive
- Existing code issues should be tracked but not block tooling setup

## Technical Design

### File Structure After Migration

```
auraframes/
├── pyproject.toml          # NEW: All config lives here
├── uv.lock                  # NEW: Lockfile (like poetry.lock)
├── .python-version          # NEW: Pin Python version for uv
├── .pre-commit-config.yaml  # NEW: Pre-commit hooks
├── .ruff.toml               # OPTIONAL: If ruff config gets large
├── tests/                   # NEW: Test directory
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_auth.py         # Login/auth tests
│   ├── test_frames.py       # Frame API tests
│   └── test_upload.py       # Upload flow tests
├── auraframes/              # Existing
├── main.py                  # Existing
└── README.md                # Update with new commands
```

### pyproject.toml Structure

```toml
[project]
name = "auraframes"
version = "0.1.0"
description = "Unofficial Python client for Aura Frames API"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.23.1",
    "h2>=4.1.0",
    "boto3>=1.26.38",
    "pydantic>=1.10.4,<2.0",  # Pin to v1, v2 has breaking changes
    "Pillow>=9.5.0",
    "piexif>=1.1.3",
    "geopy>=2.3.0",
    "tqdm>=4.65.0",
    "loguru>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0",
    "boto3-stubs[s3,sqs,cognito-identity]",  # Type stubs for AWS
    "types-Pillow",
    "types-tqdm",
]

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = [
    "boto3.*",
    "botocore.*",
    "geopy.*",
    "piexif.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - boto3-stubs[s3,sqs,cognito-identity]
          - types-Pillow
          - types-tqdm
```

### .python-version

```
3.10
```

## Testing Strategy

### Core Flow Tests (Priority Order)

1. **test_auth.py** - Login flow
   - Successful login sets auth headers
   - Invalid credentials raise appropriate error
   - Token/session management

2. **test_frames.py** - Frame operations
   - Get frames returns list of Frame models
   - Get single frame by ID
   - Frame model validation (Pydantic)

3. **test_upload.py** - Upload flow (most complex)
   - Asset creation with GUID
   - S3 upload mock
   - Batch update flow

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def mock_client():
    """Mock HTTP client for API tests."""

@pytest.fixture
def sample_frame():
    """Sample Frame model for testing."""

@pytest.fixture
def sample_asset():
    """Sample Asset model for testing."""
```

### Mocking Strategy

| Component | Mock Approach |
|-----------|---------------|
| HTTP calls | `respx` or `pytest-httpx` for httpx mocking |
| AWS S3/SQS | `moto` library (AWS mock) |
| File I/O | `tmp_path` fixture |

## Implementation Plan

### Step 1: Create pyproject.toml
- Migrate dependencies from requirements.txt
- Add tool configurations (ruff, mypy, pytest)
- Pin Pydantic to v1 (v2 has breaking changes)

### Step 2: Set up uv
- Create `.python-version` file
- Run `uv sync` to create lockfile
- Delete `requirements.txt`

### Step 3: Configure pre-commit
- Create `.pre-commit-config.yaml`
- Run `pre-commit install`

### Step 4: Create test scaffold
- Create `tests/` directory structure
- Add `conftest.py` with basic fixtures
- Write one test per core flow (auth, frames, upload)

### Step 5: Run tools and assess
- Run `ruff check .` - log issues
- Run `ruff format .` - auto-format
- Run `mypy .` - assess type errors
- File GitHub issue for existing code issues

### Step 6: Update CLAUDE.md and README
- Update Quick Reference commands
- Add development setup instructions

## Commands Reference (Post-Setup)

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Add dependency | `uv add {package}` |
| Add dev dependency | `uv add --dev {package}` |
| Run project | `uv run python main.py` |
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov=auraframes` |
| Lint | `uv run ruff check .` |
| Lint and fix | `uv run ruff check . --fix` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy .` |
| Pre-commit (manual) | `pre-commit run --all-files` |

## Out of Scope (and Why)

| Item | Reason |
|------|--------|
| CI/CD config | Minimal setup first; add when pushing to shared repo |
| Coverage thresholds | Start measuring, set thresholds after baseline |
| Pydantic v2 migration | Breaking changes, separate effort |
| Async conversion | Mentioned in codebase TODOs, separate effort |
| Documentation generation | No public API, internal tool |

## Open Questions

1. **AWS credentials in tests** - Use moto for full mock, or allow integration tests with real credentials?
2. **Test data fixtures** - Should we capture real API responses for test fixtures?

---
*Authoritative spec developed using `/enrich-plan`. Future implementers should treat this document as the source of truth.*
