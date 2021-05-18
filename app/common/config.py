from dataclasses import dataclass
from os import path, environ
from common.const import (
    POSTGRES_IP_ADDR,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


@dataclass
class Config:
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = False
    TEST_MODE: bool = False
    DB_URL: str = environ.get("DB_URL", f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_IP_ADDR}/{POSTGRES_DB}")


@dataclass
class LocalConfig(Config):
    ...


@dataclass
class ProdConfig(Config):
    ...


def config():
    config = dict(production=ProdConfig(), local=LocalConfig())
    return config.get(environ.get("API_ENV", "local"))