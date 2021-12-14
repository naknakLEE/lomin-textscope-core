from enum import Enum
from uuid import uuid4
from datetime import datetime
from typing import Optional, List
from pydantic.main import BaseModel
from pydantic.networks import EmailStr
from pydantic import Json
from fastapi.param_functions import Form

class InferenceTypeEnum(Enum):
    DU_CLS_MODEL = "cls"
    DU_KV_MODEL_1 = "kv"
    DU_KV_MODEL_2 = "kv"
    LIFE_INSURANCE = "kv"
    GENERAL_OCR = "gocr"
    RECOGNITION = "reco"
    
class InferenceSequenceEnum(Enum):
    DU_CLS_MODEL = 1
    DU_KV_MODEL_1 = 2
    DU_KV_MODEL_2 = 2
    LIFE_INSURANCE = 2
    GENERAL_OCR = 3
    RECOGNITION = 4

class UserToken(BaseModel):
    id: int
    hashed_password: str = None
    email: EmailStr = None
    name: str = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    scopes: List[str] = []


class User(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    status: str = "inactive"

    class Config:
        orm_mode = True


class UserInfo(User):
    status: Optional[Enum] = None
    is_superuser: bool = False
    id: Optional[int] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "email": "garam@example.com",
                "username": "garam",
                "full_name": "Garam Yoon",
                "status": "inactive",
                "password": "1q2w3e4r",
            }
        }


class UserRegister(User):
    password: str = None


class UserInDB(UserInfo):
    password: Optional[str] = None
    hashed_password: Optional[str] = None


class UserUpdate(User):
    status: Optional[Enum] = None
    is_superuser: bool = False
    password: str = False
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "garam@example.com",
                "username": "garam",
                "full_name": "Garam Yoon",
                "status": "inactive",
                "is_superuser": "False",
                "password": "1q2w3e4r",
            }
        }


class UsersScheme(UserInfo):
    hashed_password: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Usage(BaseModel):
    created_at: datetime
    status_code: int
    # id: Optional[int] = None
    email: EmailStr

    class Config:
        orm_mode = True


class UsageCount(BaseModel):
    total_count: int
    success_count: int
    failed_count: int


class StatusResponse(BaseModel):
    response: str = (
        f"Textscope API (is_database_working: True, is_serving_server_working: True)"
    )


class InferenceResponse(BaseModel):
    status: str
    minQlt: str
    reliability: str
    lnbzDocClcd: str
    ocrResult: dict

class PgInference(BaseModel):
    inference_pkey: int
    task_id: str
    inference_result: Optional[Json]
    inference_type: str
    create_datetime: Optional[datetime]
    image_pkey: Optional[int]
    start_datetime: Optional[datetime]
    finsh_datetime: Optional[datetime]

    class Config:
        orm_mode = True

class PgImage(BaseModel):
    image_pkey: int
    image_id: str
    image_path: str
    image_description: Optional[str]
    category_pkey: Optional[int]
    dataset_pkey: Optional[int]
    image_type: Optional[str]

    class Config:
        orm_mode = True

class CreateImage(BaseModel):
    image_id: str
    image_path: str
    image_description: Optional[str]
    
class CreateTask(BaseModel):
    task_id: str
    image_pkey: int
    
class UpdateTask(BaseModel):
    category_pkey: int
    
class CreateInference(BaseModel):
    inference_id: str
    task_pkey: int
    inference_type: str
    inference_img_path: str
    inference_result: dict
    start_datetime: datetime
    finish_datetime: datetime
    inference_sequence: int

class PgCategory(BaseModel):
    category_pkey: int
    category_name_en: Optional[str]
    category_name_kr: Optional[str]

    class Config:
        orm_mode = True

class PgDataset(BaseModel):
    dataset_pkey: int
    dataset_id: Optional[str]
    root_path: str
    zip_file_name: Optional[str]

    class Config:
        orm_mode = True




class OAuth2PasswordRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="password"),
        email: EmailStr = Form(...),
        password: str = Form(...),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret

class DocTypeHint(BaseModel):
    use: bool = True # 주어진 사전 지식을 후처리 프로세스에 사용할지 여부
    trust: bool = True # 주어진 사전 지식을 100% 신뢰할지 여부
    doc_type: str = "A01" # 서식 분류에 관한 사전지식
    
class KeyValueHint(BaseModel):
    use: bool = True # 주어진 사전 지식을 후처리 프로세스에 사용할지 여부
    trust: bool = True # 주어진 사전 지식을 100% 신뢰할지 여부
    key: str = "A01-001" # 항목 인식에 관한 사전지식 - key 코드
    value: str = "홍길동" # 항목 인식에 관한 사전지식 - value 값

class Hint(BaseModel):
    doc_type: DocTypeHint
    key_value: KeyValueHint
    
class ResponseMetadata(BaseModel):
    request_datetime: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    response_datetime: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    time_elapsed: str = '0.0001'
    
class DocType(BaseModel):
    code: str = 'A01'
    name: str = '주민등록증'
    confidence: float = 0.98
    is_hint_used: bool = False
    is_hint_trusted: bool = False
    
class Bbox(BaseModel):
    x: float = 112.0
    y: float = 177.6
    w: float = 298.3
    h: float = 223.1
    
class Task(BaseModel):
    task_id: str = str(uuid4())
    status_code: str = 'test code'
    status_message: str = 'test messgage'
    progress: float = 0.98345
    started_datetime: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    finished_datetime: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
class KeyValue(BaseModel):
    id: str = 'kv-001'
    key: str = '주소'
    confidence: float = 0.8345
    text_ids: List[str] = ['txt-0001']
    text: str = '서울특별시 서초구 서초대로 396'
    bbox: Bbox = Bbox()
    is_hint_used: bool = False
    is_hint_trusted: bool = False
    
class Text(BaseModel):
    id: str = 'txt-0001'
    text: str = '홍길동'
    bbox: Bbox = Bbox()
    confidence: float = 0.23457
    kv_ids: List[str] = ['kv-001']
    
class Dataset(BaseModel):
    image_id: str = str(uuid4())
    category_id: str = 'GV_CBR'
    category_name: str = '사업자등록증'
    filename: str = 'myfilename.jpg'
    
class Image(BaseModel):
    filename: str = 'myfilename.jpg'
    width: int = 1920
    height: int = 1080
    upload_datetime: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    format: str = 'jpg'
    data: str = 'encoded str by base64'
    
class Category(BaseModel):
    code: str = 'A01'
    name: str = '주민등록증'

class Error(BaseModel):
    error_code: str = 'ER-TRN-CLS-0002'
    error_message: str = 'dataset_id에 해당하는 데이터셋이 존재하지 않음'
    
class PredictionResponse(BaseModel):
    doc_type: DocType = DocType()
    key_values: List[KeyValue] = [KeyValue()]
    texts: List[Text] = [Text()]
    
class BaseTextsResponse(BaseModel):
    texts: List[Text] = [Text()]
    
class BaseResponse(BaseModel):
    request: dict = {}
    response_metadata: ResponseMetadata = ResponseMetadata()
    
class BaseCategoriesResponse(BaseResponse):
    categories: List[Category] = [Category()]
    
class ClassificationResponse(BaseResponse):
    doc_type: DocType = DocType()
    
class BasePredictionResponse(BaseResponse):
    prediction: PredictionResponse = PredictionResponse()
    
class ClassificationPredictionResponse(BasePredictionResponse):
    task: Task = Task()
    
class BaseTaskResponse(BaseResponse):
    task: Task = Task()
    
class GeneralOCRResponse(BaseResponse):
    prediction: BaseTextsResponse = BaseTextsResponse()
    task: Task = Task()
    image: Optional[str] = 'encoded str by base64'
    
class BaseDatasetResponse(BaseResponse):
    dataset: Dataset = Dataset()
    
class BaseImageResponse(BaseResponse):
    image: Image = Image()
    
class CommonErrorResponse(BaseResponse):
    error: Error = Error()
    
class RecificationOption(BaseModel):
    '''
    rotation_90n:
        90도 단위의 문서 회전 보정 전처리 수행.
        문서의 방향을 예측할 수 없는 경우 true,
        항상 정방향이라고 가정할 수 있는 경우 false로 지정하여 연산 시간을 절약할 수 있습니다.
    rotation_fine:
        1도 단위의 문서 회전 미세 보정 전처리 수행.
        문서의 각도를 예측할 수 없거나 정밀한 각도 보정으로 인식률을 높이고자 하는 경우 true로 지정합니다.
        문서의 각도를 보정하지 않아도 인식률이 충분히 높거나 문서가 항상 정렬된 경우 false로 지정하여 연산 시간을 절약할 수 있습니다.
    '''
    rotation_90n: bool = False
    rotation_fine: bool = False

class BaseFileResponse(BaseResponse):
     file: bytes  # 파일 첨부

class ParamPostUploadClsTrainDataset(BaseModel):
    file: bytes  # 파일 첨부
    dataset_id: str = "ea67a273-cb29-4c79-9739-708bf6085720" # UUID 형식의 데이터셋 ID
    description: Optional[str] = "서식분류 모델 3차 학습 데이터셋" # 데이터셋을 설명하는 자유 문구
    
class ParamPostTrainCls(BaseModel):
    task_id: str = "ea67a273-cb29-4c79-9739-708bf6085720" #  UUID 형식의 학습 task 고유 ID
    dataset_id: str = "ea67a273-cb29-4c79-9739-708bf6085720" #  UUID 형식의 데이터셋 ID
    description: Optional[str] = "서식분류 모델 2차 학습 (주민등록증 이미지 10장 추가)" # 모델 학습 task를 설명하는 자유 문구

class ParamPostInferenceClsKv(BaseModel):
    task_id: str = "ea67a273-cb29-4c79-9739-708bf6085720" # UUID 형식의 학습 task 고유 ID
    image_id: str = "54d5093d-ff09-44a1-9f6d-a272eee15f07" # 추론 대상 이미지 ID
    rectify: RecificationOption # 회전 보정을 통한 이미지 전처리 여부 옵션
    hint: Optional[DocTypeHint] # 후보정을 통해 인식률을 높일 수 있도록 사전지식 제공

class ParamPostInferenceGocr(BaseModel):
    image_id: str = "54d5093d-ff09-44a1-9f6d-a272eee15f07" # 인식 대상 이미지의 고유 식별 ID

class ParamPostUploadImage(BaseModel):
    file: str # 파일 첨부
    image_id: str = "ea67a273-cb29-4c79-9739-708bf6085720" # UUID 형식의 이미지 ID
    description: Optional[str] = "서식분류 모델 3차 학습 데이터셋" # 데이터셋을 설명하는 자유 문구
    