import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel, Field, PostgresDsn

TEST = "pytest" in sys.modules


class Config(BaseModel, frozen=True):
    PROD: bool = False
    POSTGRES_URL: PostgresDsn
    JWT_SECRET: str = Field(min_length=40)


def get_config() -> Config:
    """Get singleton Config"""
    global _config
    if _config:
        return _config

    _ = load_dotenv(".env.test" if TEST else ".env")
    _config = Config.model_validate(os.environ, extra="ignore")
    return _config


_config: Config | None = None
