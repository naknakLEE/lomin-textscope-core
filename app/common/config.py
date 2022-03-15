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
class DevConfig(Config):
    DB_URL: str = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@postgres:{settings.POSTGRES_IP_PORT}/{settings.POSTGRES_DATABASE}"

@dataclass
class ProdConfig(Config):
    DB_URL: str = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_IP_ADDR}:{settings.POSTGRES_IP_PORT}/{settings.POSTGRES_DATABASE}"


def config() -> Any:
    config = dict(production=ProdConfig(), dev=DevConfig(), test=TestConfig())
    return config.get(os.getenv("API_ENV", "production"))
