import os, sys
import json
import ast

try:
    from crypto.decipher import Decipher
except ImportError:
    Decipher = None

class Result(object):
    """
        base element in storage_queue for pickleable
    """
    def __init__(self, 
                 filename,
                 stream,
                 result,
                 result_key
                ):
        self.filename = filename
        self.stream = stream
        self.result = result
        self.key = result_key

    def save(self, dst, buffer_size=16384):
        # Based on FileStorage in werkzeug/datastructures.py
        with open(dst, "wb") as f:
            f.write(self.stream)

    def save_json(self, dst):
        with open(dst, mode='w', encoding='utf-8') as f:
            self.result['user']['created_at'] = self.result['user']['created_at'].strftime('%Y%m%d_%H%M%S')
            self.result['user']['updated_at'] = self.result['user']['updated_at'].strftime('%Y%m%d_%H%M%S')
            f.write(json.dumps(self.result, ensure_ascii=False))


class Config():
    # BASE CONFIG
    DEVELOP = True

    # AUTH CONFIG
    USE_AUTH = False # Default user as admin user
    USE_CUSTOM_AUTH = True
    CUSTOM_AUTH_JWT_SECRET = "hEITTdyku5"
    CUSTOM_ADMIN_USERNAME = "lomin"
    CUSTOM_ADMIN_EMAIL = "lomin@lomin.ai"
    CUSTOM_ADMIN_PASSWORD = "lomin_password"
    CUSTOM_JWT_EXP_DELTA = 3600

    # AWS CONFIG
    AWS_REGION = "ap-northeast-2"
    USER_POOL_ID = "ap-northeast-2_GJepe7y3M"
    COGNITO_AUD = "3onoh5gd2o5nrudna9r20k6lku"

    # DB CONFIG
    USE_DB = False
    if sys.platform == 'win32':
        SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432"
    else:
        SQLALCHEMY_DATABASE_URI = "postgres://postgres:postgres@postgres:5432"
    INFERENCE_DB_MAX_NUM = 1000

    # STORAGE CONFIG
    USE_STORAGE = False
    STORAGE_PATH = "storage"
    STORAGE_MAX_SIZE = 20 # in MB
    STORAGE_BACKUP_RATIO = 0.5

    STORAGE_BACKUP_USE = True
    STORAGE_HOST = "0.0.0.0"
    STORAGE_KEY_PATH = "etc/storage/storage_key"

    # DEV CONFIG
    DUMMY_RESPONSE_PATH = "./etc/dummy_response.json"

    # LOGGER CONFIG
    LOG_DIR_PATH = "storage/log"
    LOG_ROTATION = "1MB"
    LOG_RETENTION = "30 days"
    LOG_LEVEL = "DEBUG"

    # OUTPUT_IMG_CONFIG
    OUTPUT_IMG_SAVE = True
    OUTPUT_IMG_DIR = "storage/image"
    OUTPUT_DEBUG = "storage/debug"

    # TRITON SERVER CONFIG
    USE_TRITON_SERVER = False
    TRT_PROTOCOL = "http"
    TRT_URL = "triton_server:8000"

    # SERVICE CONFIG
    SERVICE_CFG_PATH = "./etc/service/textscope_id.json"
    # Do not change this value!
    USE_ENCRYPT = False
    RESOURCE_KEY = b'7Pk0EFDCapTM_p7sTWdrC7lVf6Xueqk0PV2sN9Yd5Y0='
    RESOURCE_PREFIX = "lo_"

    SAVE_UID = 1000
    SAVE_GID = 1000
    DE_ID_SAVE_PATH = "storage/image"
    DE_ID_LIMIT_SIZE = True
    DE_ID_MAX_SIZE = 640

    SAVE_INPUT_IMAGE = False
    INPUT_SAVE_PATH = "storage/image"

    SAVE_ID_DEBUG_INFO = False
    ID_DEBUG_INFO_PATH = "/tmp/textscope/debug"

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
    ID_CROP_FIND_RATIO = 0.7071 # 1/sqrt(2)

    ID_ROTATE_FIND = True
    ID_ROTATE_ANGLE = [-45, 45]
    
    DOC_DUMMY_OUTPUT = False

    DOC_KV_SCORE_TH = 0.5
    DOC_BOX_EXPANSION = 0.3

    DOC_USE_LONG_REC_MODEL = True
    DOC_LONG_REC_ASPECT_RATIO = 4.0
    
    DOC_PAGE_NUM_LIMIT = 10

    DOC_CHECK_DOCTYPE = False

    # Do not change this value!
    CHECK_LICENSE = True

    PROFILE = False

    DEIDENTIFY_JSON = True

    TIMEOUT = 1500

    RESPONSE_LOG = True

    def update_config_env_vars(self):
        env_registry = [i for i in dir(self) if not callable(i) and i[0] !='_' and i[0].isupper()]
        # logger.info("="*80)
        # logger.info("UPDATE config with enviroment variables")
        for env_name in env_registry:
            assert type(env_name) == str
            env_var = os.getenv(env_name)
            if env_var is not None:
                num_var = self.check_number(env_var)
                if env_var.lower() in ["true", "false"]:
                    env_var = ast.literal_eval(env_var.capitalize())
                elif num_var is not None:
                    env_var = num_var
                setattr(self, env_name, env_var)
            # too dangerous to log key strings
            # logger.debug(f"SET {env_name}: {getattr(self, env_name)}")
        self.DECIPHER = Decipher(key=self.RESOURCE_KEY, prefix=self.RESOURCE_PREFIX) if Decipher and self.USE_ENCRYPT else None
        # logger.info("UPDATE config done")

    def set_dependent_config(self):
        # DEPENDENT_CONFIG
        self.COGNITO_PUBKEY_URL = f"https://cognito-idp.{self.AWS_REGION}.amazonaws.com/{self.USER_POOL_ID}/.well-known/jwks.json"
        self.STORAGE_BACKUP_THRESH = float(self.STORAGE_BACKUP_RATIO)*int(self.STORAGE_MAX_SIZE)
    
    def check_number(self, x):
        try:
            y = float(x)
        except ValueError:
            return None
        else:
            if x.isnumeric():
                return int(x)
            else:
                return float(x)
