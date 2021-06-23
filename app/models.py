from enum import Enum

from datetime import datetime
from typing import Optional, List
from jose.utils import int_arr_to_long
from pydantic.main import BaseModel
from pydantic.networks import EmailStr
from pydantic import Json
from fastapi.param_functions import Form


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


class UsersScheme(UserInfo):
    hashed_password: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Usage(BaseModel):
    created_at: datetime
    status_code: int
    # id: Optional[int] = None
    email: str

    class Config:
        orm_mode = True


class UsageCount(BaseModel):
    total_count: int
    success_count: int
    failed_count: int


class StatusResponse(BaseModel):
    response: str = f"Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))"


class InferenceResponse(BaseModel):
    status: str
    minQlt: str
    reliability: str
    docuType: str
    ocrResult: dict


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
