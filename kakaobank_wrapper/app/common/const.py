from typing import List, Optional, Any
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
    KAKAO_WRAPPER_IP_ADDR: str
    POSTGRES_IP_ADDR: str
    MYSQL_IP_ADDR: str
    WEB_IP_ADDR: str
    SERVING_IP_ADDR: str
    REDIS_IP_ADDR: str
    PP_IP_ADDR: str

    # POSTGRESQL CONFIG
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # MYSQL CONFIG
    MYSQL_ROOT_USER: str
    MYSQL_DB: str
    MYSQL_PASSWORD: str

    # SERVING CONFIG
    KAKAO_WRAPPER_IP_PORT: int
    SERVING_IP_PORT: int
    REDIS_IP_PORT: int
    WEB_IP_PORT: int
    PP_IP_PORT: int

    # BASE CONFIG
    DEVELOP: bool = True
    API_ENV: str = "production"
    BASE_PATH: str = "."

    # KAKAOBANK_WRAPPER_CONFIG
    DOCUMENT_TYPE_LIST = ["D01", "D02", "D53", "D54"]

    DOCUMENT_TYPE_SET = {
        "D01": "rrtable",
        "D02": "family_cert",
        "D53": "basic_cert",
        "D54": "regi_cert",
    }

    # LOGGER CONFIG
    LOG_DIR_PATH: str = f"{BASE_PATH}/logs/kakaobank_wrapper"
    LOG_ROTATION: str = "1MB"
    LOG_RETENTION: str = "30 days"
    FILE_MAX_BYTE: int = 1024 * 1024
    BACKUP_COUNT: int = 100000000
    LOG_LEVEL: str = "DEBUG"
    BACKTRACE: str = "True"
    DIAGNOSE: str = "True"
    ENQUEUE: str = "True"
    COLORIZE: str = "True"
    SERIALIZE = "serialize"
    ENCODING: str = "utf-8"
    FORMAT: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
