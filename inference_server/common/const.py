from typing import List, Optional, Any
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # # DOCKER SERVER ADDRESS
    # POSTGRES_IP_ADDR: str
    # MYSQL_IP_ADDR: str
    # WEB_IP_ADDR: str
    # SERVING_IP_ADDR: str
    # REDIS_IP_ADDR: str
    # PP_IP_ADDR: str

    # # POSTGRESQL CONFIG
    # POSTGRES_DB: str
    # POSTGRES_USER: str
    # POSTGRES_PASSWORD: str

    # # MYSQL CONFIG
    # MYSQL_ROOT_USER: str
    # MYSQL_DB: str
    # MYSQL_PASSWORD: str

    # # AUTHORIZATION SETTING
    # SECRET_KEY: str
    # ALGORITHM: str
    # ACCESS_TOKEN_EXPIRE_MINUTES: int

    # # ACCESS KEY
    # AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    # # SERVING CONFIG
    # SERVING_IP_PORT: int
    # REDIS_IP_PORT: int
    # WEB_IP_PORT: int
    # PP_IP_PORT: int

    # # BASE CONFIG
    # DEVELOP: bool = True
    # API_ENV: str = "production"
    # BASE_PATH: str = "."
    # DOCKER SERVER ADDRESS
    KAKAO_WRAPPER_IP_ADDR = "182.20.0.19"
    PP_IP_ADDR = "182.20.0.18"
    REDIS_IP_ADDR = "182.20.0.17"
    MYSQL_EXPORTER_IP_ADDR = "182.20.0.16"
    MYSQL_IP_ADDR = "182.20.0.15"
    NGINX_IP_ADDR = "182.20.0.14"
    NODE_EXPORTER_IP_ADDR = "182.20.0.13"
    DCGM_EXPORTER_IP_ADDR = "182.20.0.12"
    POSTGRES_EXPORTER_IP_ADDER = "182.20.0.11"
    GRAFANA_IP_ADDR = "182.20.0.10"
    PROMETHEUS_IP_ADDR = "182.20.0.9"
    PGADMIN_IP_ADDR = "182.20.0.8"
    POSTGRES_IP_ADDR = "182.20.0.6"
    WEB_IP_ADDR = "182.20.0.5"
    SERVING_IP_ADDR = "182.20.0.4"

    # POSTGRESQL CONFIG
    POSTGRES_DB = "test"
    POSTGRES_USER = "admin"
    POSTGRES_PASSWORD = "1q2w3e4r"

    # MYSQL CONFIG
    MYSQL_ROOT_USER = "root"
    MYSQL_DB = "admin"
    MYSQL_PASSWORD = "1q2w3e4r"

    # AUTHORIZATION SETTING
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 600

    # ACCESS KEY
    AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=cs1100320013a1502d2;AccountKey=sl2JAk7SdA8Wf7/o1gIw5jfM0UaA+C5F16UfdDvkeC/9EE1CkhTSIRYoNdUBMy49Racupj9H/E+YnN6WKTYk0g==;EndpointSuffix=core.windows.net"

    # SERVING CONFIG
    SERVING_IP_PORT = 5000
    WEB_IP_PORT = 8000
    PP_IP_PORT = 8080
    REDIS_IP_PORT = 6379

    # BASE CONFIG
    DEVELOP = True
    BASE_PATH = "."

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

    # LOGGER CONFIG
    LOG_DIR_PATH: str = f"{BASE_PATH}/logs/model_service/log"
    LOG_ROTATION: str = "1MB"
    LOG_RETENTION: str = "30 days"
    LOG_LEVEL: str = "DEBUG"
    FILE_MAX_BYTE: int = 1024 * 1024
    BACKUP_COUNT: int = 100000000

    # OUTPUT_IMG_CONFIG
    OUTPUT_IMG_SAVE: bool = True
    OUTPUT_IMG_DIR: str = f"{BASE_PATH}/outputs/image"
    OUTPUT_DEBUG: str = f"{BASE_PATH}/outputs/debug"

    # SERVICE CONFIG
    SERVICE_TYPE = "textscope_document"
    SERVICE_CFG_PATH: str = f"{BASE_PATH}/assets/{SERVICE_TYPE}.json"
    SERVICE_ENV_PATH: str = f"{BASE_PATH}/.env"

    # OTHERS
    PROFILING_TOOL: str = "cProfile"
    PYINSTRUMENT_RENDERER: str = "html"

    SAVE_INPUT_IMAGE: bool = False
    INPUT_SAVE_PATH: str = f"{BASE_PATH}/inputs/image"
    SAVEPATH: str = f"{BASE_PATH}/outputs/idcard/test.png"

    SAVE_ID_DEBUG_INFO: bool = False
    ID_DEBUG_INFO_PATH: str = f"{BASE_PATH}/tmp/textscope/debug"

    # MODEL CONFIG
    DOCUMENT_DETECTION_SCORE_THRETHOLD: float = 0.3
    SAVE_DOCUMENT_VISULAIZATION_IMG: bool = True

    SAVE_UID: int = 1000
    SAVE_GID: int = 1000
    DE_ID_SAVE_PATH: str = f"{BASE_PATH}/inputs/image"
    DE_ID_LIMIT_SIZE: bool = True
    DE_ID_MAX_SIZE: int = 640

    ID_IMG_MIN_SIZE = 1000
    ID_BOUNDARY_SCORE_TH = 0.5
    ID_BOUNDARY_CROP_EXPANSION = 100

    ID_USE_BOUNDARY_MASK_TRANSFORM = True
    ID_BOUNDARY_MASK_FORCE_RECT = False
    ID_BOUNDARY_MASK_THRESH = 0.5
    ID_USE_TRANSFORM_BOUNDARY = True
    ID_TRANSFORM_TARGET_WIDTH = 1000
    ID_TRANSFORM_TARGET_HEIGHT = 628

    ID_KV_SCORE_TH = 0.3
    ID_BOX_EXPANSION = 0.2
    ID_DLC_REMOVE_REGION_CODE = False
    ID_ADD_BACKUP_BOXES = False
    ID_DRAW_BBOX_IMG = False
    ID_DE_NAME = True
    ID_FORCE_TYPE = False

    ID_CROP_FIND = True
    ID_CROP_FIND_NUM = 3
    ID_CROP_FIND_RATIO = 0.7071  # 1/sqrt(2)

    ID_ROTATE_FIND = True
    ID_ROTATE_ANGLE = [-45, 45]

    DEIDENTIFY_JSON = True

    RESPONSE_LOG = True

    DECIPHER = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
