import os

from typing import Any
from dataclasses import dataclass
from app.common.const import get_settings


settings = get_settings()


@dataclass
class Config:
    BASE_DIR = settings.BASE_DIR
    DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE
    DB_ECHO = settings.DB_ECHO
    DEBUG = settings.DATABASE_DEBUG
    TEST_MODE = settings.TEST_MODE
    POOL_SIZE = settings.POOL_SIZE
    MAX_OVERFLOW = settings.MAX_OVERFLOW


@dataclass
class TestConfig(Config):
    TEST_MODE: bool = True
    DB_URL: str = f"sqlite:///{settings.BASE_PATH}/assets/sql_app.db"


@dataclass
class ProdConfig(Config):
    DB_URL: str = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_IP_ADDR}:{settings.MYSQL_IP_PORT}/{settings.TEXTSCOPE_SERVER_DATABASE}"


def config() -> Any:
    config = dict(production=ProdConfig(), test=TestConfig())
    return config.get(os.environ["API_ENV"])
