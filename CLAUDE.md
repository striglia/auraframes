# Aura Frames Python Client

Unofficial Python client for reverse-engineered Aura Frames digital photo frame APIs.

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run | `uv run python main.py` |
| Test | `uv run pytest` |
| Test (verbose) | `uv run pytest -v` |
| Lint | `uv run ruff check .` |
| Lint (fix) | `uv run ruff check . --fix` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy .` |
| Add dep | `uv add {package}` |
| Add dev dep | `uv add --dev {package}` |

## Architecture

```
auraframes/
├── aura.py          # Main orchestrator - start here
├── client.py        # HTTP client (httpx + HTTP/2)
├── api/             # API endpoint modules
├── models/          # Pydantic data models
├── aws/             # AWS service clients (S3, SQS, Cognito)
└── utils/           # Settings, I/O, datetime helpers
```

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point - login and basic operations |
| `auraframes/aura.py` | `Aura` class orchestrates all operations |
| `auraframes/client.py` | `Client` wraps httpx with auth headers |
| `auraframes/api/frameApi.py` | Frame CRUD, asset management, slideshow control |
| `auraframes/api/assetApi.py` | Image metadata, cropping, date modifications |
| `auraframes/models/asset.py` | `Asset` model with 100+ fields for images |
| `auraframes/aws/s3client.py` | Direct S3 uploads to `images.senseapp.co` |

### Key Patterns

- **Pydantic models everywhere** - All API responses deserialize to typed models in `models/`
- **BaseApi inheritance** - All API classes extend `BaseApi` which holds the shared `Client`
- **AWS Cognito for S3** - Uses identity pool for temporary credentials, not API keys
- **Proxy URLs for downloads** - Images retrieved via `https://imgproxy.pushd.com/`

### Data Flow

```
User → Aura (orchestrator) → API modules → Client (httpx) → api.pushd.com
                          ↘ AWS clients → S3/SQS (direct)
```

## Conventions

- **Environment variables for secrets** - `AURA_EMAIL`, `AURA_PASSWORD`, `AURA_DEVICE_IDENTIFIER`
- **Sync-only** - No async/await yet (TODO in codebase)
- **Pydantic v1 style** - Uses `BaseModel` with `Config` class, not v2 `model_config`
- **httpx not requests** - Modern HTTP client with HTTP/2 support
- **loguru for logging** - Not stdlib `logging`

## Gotchas

- **Reverse-engineered API** - Endpoints mimic Android client `Aura/4.7.790`
- **AWS pool IDs hardcoded** - See `TODO` comments in aws clients for configurability
- **Upload flow is complex** - 10-step process documented in README with sequence diagram
- **SQS polling required** - Some operations need to poll SQS between API calls
- **No error handling** - Many `# TODO: error handling` comments, failures may be silent
- **Lint/type issues exist** - See [issue #1](https://github.com/striglia/auraframes/issues/1) for cleanup

## Dependencies

| Service | Purpose |
|---------|---------|
| `api.pushd.com` | Main Aura Frames REST API |
| `images.senseapp.co` (S3) | Image storage bucket |
| `imgproxy.pushd.com` | Image proxy for downloads |
| AWS Cognito | Identity pool for S3 credentials |
| AWS SQS | Real-time event queues per frame |

## Development Notes

- **README has flow diagrams** - Check upload/download sequences before modifying those flows
- **~1,400 lines of Python** - Small codebase, easy to navigate
- **Models are comprehensive** - `Asset` model has every field from API response
- **Caching decorator exists** - `@cache_result` in `cache.py` for expensive calls
