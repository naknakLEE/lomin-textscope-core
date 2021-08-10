from typing import List, Optional, Any
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
    MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR: str
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
    TEXTSCOPE_SERVER_MYSQL_DB: str
    MYSQL_PASSWORD: str

    # AUTHORIZATION SETTING
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ACCESS KEY
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    # PORT CONFIG
    SERVING_IP_PORT: int
    REDIS_IP_PORT: int
    WEB_IP_PORT: int
    PP_IP_PORT: int
    MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_PORT: int

    # BASE CONFIG
    DEVELOP: bool = True
    API_ENV: str = "production"
    BASE_PATH: str = "/workspace"

    # OTHERS
    PROFILING_TOOL: str = "cProfile"
    PYINSTRUMENT_RENDERER: str = "html"

    # KAKAOBANK_WRAPPER_CONFIG
    DOCUMENT_TYPE_SET = {
        "D01": "rrtable",
        "D02": "family_cert",
        "D53": "basic_cert",
        "D54": "regi_cert",
    }

    # LOGGER CONFIG
    TEXTSCOPE_LOG_DIR_PATH: str
    LOG_ROTATION: str = "1MB"
    LOG_RETENTION: str = "30 days"
    LOG_LEVEL: str = "DEBUG"
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

    # FAKE DATA
    FAKE_SUPERUSER_INFORMATION: dict = {
        "username": "user",
        "full_name": "user",
        "email": "user@example.com",
        "password": "123456",
        "status": "inactive",
        "is_superuser": True,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FAKE_USER_INFORMATION: dict = {
        "username": "garam",
        "full_name": "garam",
        "email": "garam@example.com",
        "password": "123456",
        "status": "inactive",
        "is_superuser": False,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FAKE_USER_INFORMATION2: dict = {
        "username": "tongo",
        "full_name": "tongo",
        "email": "tongo@example.com",
        "password": "123456",
        "status": "inactive",
        "is_superuser": False,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    class Config:
        env_file = "/workspace/.env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
