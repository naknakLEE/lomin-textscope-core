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
    SERVICE_TYPE = "textscope_id"
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

    DECIPHER = True

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
