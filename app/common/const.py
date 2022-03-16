import json

from typing import List, Optional, Any, Dict, Tuple
from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable
from functools import lru_cache
from os import path
from pathlib import Path

base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


def json_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    encoding = settings.__config__.env_file_encoding
    customer_config = json.loads(
        Path(f"/workspace/assets/textscope.json").read_text(encoding)
    )
    config = customer_config
    return config


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
    MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR: str
    POSTGRES_IP_ADDR: str
    POSTGRES_IP_CONNET_ADDR: str
    WEB_IP_ADDR: str
    SERVING_IP_ADDR: str
    REDIS_IP_ADDR: str
    PP_IP_ADDR: str
    MYSQL_IP_ADDR: str
    REDIS_IP_PORT_ADDR: str

    # DOCKER SERVER PORT
    SERVING_IP_PORT: int
    SERVING_HEALTH_CHECK_IP_PORT: int
    REDIS_IP_PORT: int
    WEB_IP_PORT: int
    PP_IP_PORT: int
    MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_PORT: int
    MYSQL_IP_PORT: int
    POSTGRES_IP_PORT: int
    GENERAL_DETECTION_SERVICE_PORT: int = 5000
    RECOGNITION_SERVICE_PORT: int = 5000
    CLASSIFICATION_SERVICE_PORT: int = 5000
    KV_DETECTION_SERVICE_PORT: int = 5000
    ROTATE_SERVICE_PORT: int = 5000

    # POSTGRESQL CONFIG
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str

    # MYSQL CONFIG
    MYSQL_USER: str
    TEXTSCOPE_SERVER_DATABASE: str
    MYSQL_PASSWORD: str

    # DATABASE SETTING
    USE_TEXTSCOPE_DATABASE: bool = True
    USE_AUTO_LOG: bool = True

    # DATABASE CONFIG
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DATABASE_DEBUG: bool = False
    TEST_MODE: bool = False
    POOL_SIZE: int = 50
    MAX_OVERFLOW: int = 20000
    INITIAL_DB: bool = True

    # STORAGE CONFIG
    MINIO_IP_ADDR: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = "H7YX3286K2P7C8O94CM8"
    MINIO_SECRET_KEY: str = "MSJsIpHGaA4BpxMQZXUyvgx+Ci0YrLJDpCj89C3J"
    MINIO_REGION: str = "ap-northeast-2"
    CHECK_VALIDATION: bool = False

    # AUTHORIZATION SETTING
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # LDAP
    LDAP_ADMIN_USER: str = "cn=admin,dc=lomin,dc=ai"
    LDAP_ADMIN_PASSWORD: str = "lomin"

    # ACCESS KEY
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    # BASE CONFIG
    DEVELOP: bool = True
    API_ENV: str = "production"
    BASE_PATH: str = "/workspace"
    TIMEOUT_SECOND: float = 1200.0
    CUSTOMER: str
    TEXTSCOPE_CORE_WORKERS: int = 1

    # MINIO CONFIG
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_USE_SSL: bool = False
    MINIO_IMAGE_BUCKET: str = "images"
    USE_MINIO: bool = True

    # HINT CONFIG
    KV_HINT_CER_THRESHOLD: float = 0.2
    CLS_HINT_SCORE_THRESHOLD: float = 0.2

    # OCR CONFIG
    OCR_PIPELINE: bool = False
    USE_OCR_PIPELINE: bool = False

    # OTHERS
    PROFILING_TOOL: str = "cProfile"
    PYINSTRUMENT_RENDERER: str = "html"
    CLASS_MAPPING_TABLE: Dict = {}

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
    BACKUP_COUNT: int = 10
    BACKTRACE: str = "True"
    DIAGNOSE: str = "True"
    ENQUEUE: str = "True"
    COLORIZE: str = "True"
    SERIALIZE = "serialize"
    ENCODING: str = "utf-8"
    FORMAT: str = "complex"  # simple or complex

    # FAKE DATA
    FAKE_SUPERUSER_INFORMATION: Dict = {
        "username": "user",
        "full_name": "user",
        "email": "user@example.com",
        "password": "123456",
        "is_superuser": True,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FAKE_USER_INFORMATION: Dict = {
        "username": "garam",
        "full_name": "garam",
        "email": "garam@example.com",
        "password": "123456",
        "is_superuser": False,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FAKE_USER_INFORMATION2: Dict = {
        "username": "tongo",
        "full_name": "tongo",
        "email": "tongo@example.com",
        "password": "123456",
        "is_superuser": False,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FAKE_USER_INFORMATION_GUEST: Dict = {
        "username": "guest",
        "full_name": "guest",
        "email": "guest@lomin.ai",
        "password": "guest",
        "status": "ACTIVE",
        "is_superuser": False,
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    # KBCARD CONFIG
    ALLOWED_CHARACTERS_SET: Dict = {}
    LENGTH_SET: Dict = {}
    DOC_MAPPING_TABLE: Dict = {}
    DOC_TYPE_SET: Dict = {}
    LOOKUP_TABLE: Dict = {}
    VALID_TYPE: Dict = {}
    TORCH_MODEL_NAME_SET: List = []
    DOC_KEY_SET: Dict = {}
    IDCARD_TYPE_SET: List = []
    KV_TYPE_SET: Dict = {}
    PARAMETER_ERROR_SET: Dict = {}
    CLASSIFICATION_TARGET: List = []
    SPACING_KEY: List = []
    NOT_SUPPORTED_OCR_TARGET: List = []
    RETURN_CLASS_MAPPING_TABLE: Dict = {}

    DOCUMENT_TYPE_LIST: List = []
    KEYWORDS: Dict = {}
    KEYWORDS_ALL: Dict = {}
    PP_MAPPING_TABLE: Dict = {}

    # KAKAOBANK CONFIG
    ESSENTIAL_KEYS: Dict = {}
    PARAMETER_FULL_NAME_MAPPING_TABLE: Dict = {}

    # HEUNGKUK CONFIG
    DETECTION_MERGE_THRESHOLD: Tuple = (0.05, 0.5)  # x_iou, y_iou
    SUBSTITUTE_SPCHAR_TO_ALPHA: bool = False
    FORCE_MERGE_DCC_BOX: bool = False
    DURIEL_SUPPORT_DOCUMENT: List = []
    INSURANCE_SUPPORT_DOCUMENT: List = []
    COMMA_KEY: List = []
    NTOC: Dict = {}
    CTON: Dict = {}

    # FILE CONFIG
    ZIP_PATH: str
    IMG_PATH: str
    SUPPORT_SET_DIR: str
    IMAGE_VALIDATION: List = [
        ".jpg",
        ".png",
        ".pdf",
        ".tif",
        ".tiff",
        ".jpeg",
        ".jp2",
        ".bmp",
    ]
    KEY_LENGTH_TABLE: Dict = {}
    DATABASE_INITIAL_DATA: Dict = {}
    KV_CATEGORY_MAPPING: Dict = {}

    class Config:
        env_file = "/workspace/.env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                json_config_settings_source,
                env_settings,
                file_secret_settings,
            )


@lru_cache()
def get_settings() -> Any:
    return Settings()
