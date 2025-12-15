# My FastAPI Template

> It's my playground, so it uses the latest Python 3.14 and PostgreSQL 18 features.\
> This repository is a new public repo that replaces my old private repo.

Minimal template with useful things such as:
- full async setup (FastAPI, SQLAlchemy, Alembic, pytest)
- config with automatic loading and validation of `.env` and `.env.test`
- pytest in multi-worker mode with database isolation
- database & auth utils

- preconfigured logging 
  - bounded context vars per request
  - JSON serialization when `PROD=1`

- module with scripts
  - `uv run -m scripts.gen_env` outputs a template env file based on the config class

## Stack

- Framework: FastAPI
- Server: Uvicorn/Gunicorn
- ORM: SQLAlchemy
- Migrations: Alembic
- Database: PostgreSQL
- Database Driver: psycopg
- Logging: structlog
- Tests: pytest, pytest-xdist
- Type Checker: basedpyright
- Linter & Formatter: ruff

## Configuration
> To see all env variable details, go to [app/config.py](app/config.py)

Generate template .env files using the command below and then populate them.
```bash
uv run -m scripts.gen_env | tee .env .env.test
```

## Run
```bash
# Uvicorn Development
uv run uvicorn app.app:app

# Gunicorn/Uvicorn Production
uv run gunicorn app.app:app -c gunicorn.conf.py
```

## Development
```bash
# Test
uv run pytest
uv run pytest -n auto # multi-worker mode

# Lint
uv run ruff check --fix --select F401,E402

# Type check
uv run basedpyright
```



