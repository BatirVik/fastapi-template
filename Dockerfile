FROM python:3.14-slim AS builder

WORKDIR /build

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-group dev


FROM python:3.14-slim

WORKDIR /service

ENV VIRTUAL_ENV="/servive/.venv" PATH="/service/.venv/bin:$PATH"

COPY --from=builder /build/.venv ./.venv
COPY app ./app
COPY gunicorn.conf.py pyproject.toml ./

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "app.app:app", "-c", "gunicorn.conf.py"]




