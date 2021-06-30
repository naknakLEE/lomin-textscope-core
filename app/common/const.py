from typing import List, Optional, Any
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
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

    # AUTHORIZATION SETTING
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ACCESS KEY
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    # SERVING CONFIG
    SERVING_IP_PORT: int
    REDIS_IP_PORT: int
    WEB_IP_PORT: int
    PP_IP_PORT: int

    # BASE CONFIG
    DEVELOP: bool = True
    API_ENV: str = "production"
    BASE_PATH: str = "."

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
    LOG_DIR_PATH: str = "logs/log"
    LOG_ROTATION: str = "1MB"
    LOG_RETENTION: str = "30 days"
    LOG_LEVEL: str = "DEBUG"
    FILE_MAX_BYTE: int = 1024 * 1024
    BACKUP_COUNT: int = 100000000

    # OUTPUT_IMG_CONFIG
    OUTPUT_IMG_SAVE: bool = True
    OUTPUT_IMG_DIR: str = "outputs/image"
    OUTPUT_DEBUG: str = "outputs/debug"

    # SERVICE CONFIG
    SERVICE_TYPE = "textscope_document"
    SERVICE_CFG_PATH: str = f"{BASE_PATH}/assets/{SERVICE_TYPE}.json"
    SERVICE_ENV_PATH: str = f"{BASE_PATH}/.env"

    # OTHERS
    PROFILING_TOOL: str = "cProfile"
    PYINSTRUMENT_RENDERER: str = "html"

    SAVE_INPUT_IMAGE: bool = False
    INPUT_SAVE_PATH: str = "inputs/image"
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

    ID_IMG_MIN_SIZE: int
    ID_BOUNDARY_SCORE_TH: float
    ID_BOUNDARY_CROP_EXPANSION: int

    ID_USE_BOUNDARY_MASK_TRANSFORM: bool
    ID_BOUNDARY_MASK_FORCE_RECT: bool
    ID_BOUNDARY_MASK_THRESH: float
    ID_USE_TRANSFORM_BOUNDARY: bool
    ID_TRANSFORM_TARGET_WIDTH: int
    ID_TRANSFORM_TARGET_HEIGHT: int

    ID_KV_SCORE_TH: float
    ID_BOX_EXPANSION: float
    ID_DLC_REMOVE_REGION_CODE: bool
    ID_ADD_BACKUP_BOXES: bool
    ID_DRAW_BBOX_IMG: bool
    ID_DE_NAME: bool
    ID_FORCE_TYPE: bool

    ID_CROP_FIND: bool
    ID_CROP_FIND_NUM: int
    # ID_CROP_FIND_RATIO: float  # 1/sqrt(2)

    ID_ROTATE_FIND: bool
    ID_ROTATE_ANGLE: List[int]

    DEIDENTIFY_JSON: bool = True

    RESPONSE_LOG: bool = True

    DECIPHER: bool = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
