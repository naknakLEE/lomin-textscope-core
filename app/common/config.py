from typing import Any
from dataclasses import dataclass
from os import path, environ
from app.common.const import get_settings


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
    # DB_URL: str = environ.get("DB_URL", f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_IP_ADDR}/test")
    TEST_MODE: bool = True
    DB_URL: str = "sqlite:///./sql_app.db"


@dataclass
class ProdConfig(Config):
    DB_URL: str = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_IP_ADDR}/{settings.POSTGRES_DB}"


def config() -> Any:
    config = dict(production=ProdConfig(), test=TestConfig())
    return config.get(settings.API_ENV)
