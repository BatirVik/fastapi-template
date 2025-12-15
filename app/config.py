import os
import sys
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, PostgresDsn

TEST = "pytest" in sys.modules


class Config(BaseModel, frozen=True):
    PROD: bool = False

    DB_URL: PostgresDsn
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10

    JWT_SECRET: str


@lru_cache
def get_config() -> Config:
    _ = load_dotenv(".env.test" if TEST else ".env")
    config = Config.model_validate(os.environ, extra="ignore")
    return config
