import logging
import time
import tomllib
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid7

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.config import get_config
from app.database.core import DB
from app.logger import configure_logger, logger

config = get_config()

level = logging.INFO if config.PROD else logging.DEBUG
configure_logger(level, config.PROD)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not config.PROD:
        logger.warning("config.PROD == False")

    await DB.connect(config.DB_URL.encoded_string())
    yield
    await DB.disconnect()


pyproject = tomllib.load(open("pyproject.toml", "rb"))


app = FastAPI(
    title=pyproject["project"]["name"],
    description=pyproject["project"]["description"],
    version=pyproject["project"]["version"],
    redirect_slashes=False,
    lifespan=lifespan,
    redoc_url=None if config.PROD else "/redoc",
    docs_url=None if config.PROD else "/docs",
    openapi_url=None if config.PROD else "/openapi.json",
)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    structlog.contextvars.clear_contextvars()
    _ = structlog.contextvars.bind_contextvars(req_id=uuid7().hex)

    if xff := request.headers.get("x-forwarded-for"):
        ip = xff.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = None

    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled Exception")
        response = JSONResponse({"detail": "Internal Server Error"}, 500)

    elapsed = time.perf_counter() - start

    if elapsed > 1:
        logger.warning("Request handling took longer than 1 second", elapsed=elapsed)

    logger.info(
        "HTTP request",
        ip=ip,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        elapsed=f"{elapsed:.2f}s",
    )
    return response


@app.get("/")
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/health", status_code=204)
def health():
    pass
