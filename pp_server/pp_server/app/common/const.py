from typing import Dict, List, Optional, Any
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
    PP_SERVER_MYSQL_DB: str
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
    PP_SERVER_APP_NAME = "pp_server"
    PP_DEBUGGING: bool = False  # profiling or base

    # LOGGER CONFIG
    PP_LOG_DIR_PATH: str
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

    # IDCARD AND DOCUMENT CONFIG
    ID_DLC_REMOVE_REGION_CODE: bool = False
    DEIDENTIFY_JSON: bool = True
    ID_DE_NAME: bool = True
    VALID_TYPE: Dict = {
        "RRC": ["id", "issue_date", "name"],
        "DLC": [
            "id",
            "issue_date",
            "name",
            "dlc_license_region",
            "dlc_license_num",
            "dlc_serial_num",
        ],
        "ARC_FRONT": ["id", "issue_date", "name", "arc_nationality", "arc_visa"],
        "ARC_BACK": ["expiration_date"],
        "REPRESENTATIVE_ID": [
            "dlc_title",
            "name",
            "dlc_regnum",
            "dlc_issue_date",
            "dlc_license_num",
            "dlc_exp_date",
        ],
        "GENERAL_OCR": [
            "dlc_title",
            "name",
            "dlc_regnum",
            "dlc_issue_date",
            "dlc_license_num",
            "dlc_exp_date",
        ],
        "TRANSACTION_BANK_BOOK": [
            "page_outline",
            "bank_name_value",
            "account_name_key",
            "account_name_value",
            "account_type_key",
            "account_type_value",
            "account_num_key",
            "account_num_value",
        ],
        "BUSINESS_REGISTRATION": [
            "business_num_key",
            "business_num_value",
            "business_name_key",
            "business_name_value",
            "business_repre_key",
            "business_repre_value",
            "business_address_key",
            "business_address_value",
            "business_addresshq_key",
            "business_addresshq_value",
            "business_workcond_key",
            "business_workcond_value",
            "business_worktype_key",
            "business_worktype_value",
            "business_bdate_key",
            "business_bdate_value",
            "business_type_value",
            "business_issuedate_value",
        ],
    }

    ESSENTIAL_KEYS: Dict = {
        "RRC": ["id", "name", "issue_date"],
        "DLC": ["id", "issue_date", "name", "dlc_license_num"],
        "ARC_FRONT": ["id", "issue_date", "name", "arc_nationality"],
        "ARC_BACK": ["expiration_date"],
    }

    class Config:
        env_file = "/workspace/.env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
