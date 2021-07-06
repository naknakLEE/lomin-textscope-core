import os

from typing import Any
from dataclasses import dataclass
from os import path
from pp_server.app.common.const import get_settings


settings = get_settings()
base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


@dataclass
class Config:
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = False
    TEST_MODE: bool = False


@dataclass
class TestConfig(Config):
    TEST_MODE: bool = True
    DB_URL: str = "sqlite:///./assets/sql_app.db"


@dataclass
class ProdConfig(Config):
    DB_URL: str = f"mysql://{settings.MYSQL_ROOT_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_IP_ADDR}/{settings.MYSQL_DB}"


def config() -> Any:
    config = dict(production=ProdConfig(), test=TestConfig())
    return config.get(os.environ["API_ENV"])
