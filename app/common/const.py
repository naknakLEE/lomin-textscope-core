from typing import List, Optional
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
    POSTGRES_IP_ADDR: str
    WEB_IP_ADDR: str
    SERVING_IP_ADDR: str

    # POSTGRESQL CONFIG
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # AUTHORIZATION SETTING
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # SERVING CONFIG
    SERVING_IP_PORT: int

    # MiDDLEWARE CONFIG
    EXCEPT_PATH_LIST: List[str] = ["/", "/openapi.json"]
    EXCEPT_PATH_REGEX: str = "^(/docs|/redoc|/api/auth)"

    FAKE_INFORMATION: dict = {
        "username": "user",
        "full_name": "user",
        "email": "user@example.com",
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

    FILE_MAX_BYTE: int = 1024 * 1024
    BACKUP_COUNT: int = 100000000

    LOGGER_LEVEL: str = "DEBUG"

    # BASE CONFIG
    DEVELOP: bool = True
    BASE_PATH: str

    # LOGGER CONFIG
    LOG_DIR_PATH: str
    LOG_ROTATION: str
    LOG_RETENTION: str
    LOG_LEVEL: str

    # OUTPUT_IMG_CONFIG
    OUTPUT_IMG_SAVE: bool
    OUTPUT_IMG_DIR: str
    OUTPUT_DEBUG: str

    # SERVICE CONFIG
    SERVICE_CFG_PATH: str

    # OTHERS
    PROFILING: str

    SAVE_INPUT_IMAGE: Optional[bool]
    INPUT_SAVE_PATH: Optional[str]
    SAVEPATH: Optional[str]

    SAVE_ID_DEBUG_INFO: Optional[bool]
    ID_DEBUG_INFO_PATH: Optional[str]

    SAVE_UID: Optional[int]
    SAVE_GID: Optional[int]
    DE_ID_SAVE_PATH: Optional[str]
    DE_ID_LIMIT_SIZE: Optional[bool]
    DE_ID_MAX_SIZE: Optional[int]

    ID_IMG_MIN_SIZE: Optional[int]
    ID_BOUNDARY_SCORE_TH: Optional[float]
    ID_BOUNDARY_CROP_EXPANSION: Optional[int]

    ID_USE_BOUNDARY_MASK_TRANSFORM: Optional[bool]
    ID_BOUNDARY_MASK_FORCE_RECT: Optional[bool]
    ID_BOUNDARY_MASK_THRESH: Optional[float]
    ID_USE_TRANSFORM_BOUNDARY: Optional[bool]
    ID_TRANSFORM_TARGET_WIDTH: Optional[int]
    ID_TRANSFORM_TARGET_HEIGHT: Optional[int]

    ID_KV_SCORE_TH: Optional[float]
    ID_BOX_EXPANSION: Optional[float]
    ID_DLC_REMOVE_REGION_CODE: Optional[bool]
    ID_ADD_BACKUP_BOXES: Optional[bool]
    ID_DRAW_BBOX_IMG: Optional[bool]
    ID_DE_NAME: Optional[bool]
    ID_FORCE_TYPE: Optional[bool]

    ID_CROP_FIND: Optional[bool]
    ID_CROP_FIND_NUM: Optional[int]
    ID_CROP_FIND_RATIO: Optional[float]  # 1/sqrt(2)

    ID_ROTATE_FIND: Optional[bool]
    ID_ROTATE_ANGLE: Optional[List[int]]

    DEIDENTIFY_JSON: Optional[bool]

    RESPONSE_LOG: Optional[bool]

    DECIPHER: Optional[bool]

    class Config:
        env_file = "/workspace/.env"


@lru_cache()
def get_settings():
    return Settings()
