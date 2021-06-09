from datetime import datetime
from typing import Optional, List
from jose.utils import int_arr_to_long
from pydantic.main import BaseModel
from pydantic.networks import EmailStr


class UserToken(BaseModel):
    id: int
    hashed_password: str = None
    email: EmailStr = None
    name: str = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None


class User(BaseModel):
    email: EmailStr = None
    username: Optional[str]
    full_name: Optional[str] = None

    class  Config:
        orm_mode = True

class UserInfo(User):
    disabled: bool = False
    is_active: Optional[bool] = None
    is_superuser: bool = False
    id: Optional[int] = None

    class  Config:
        orm_mode = True


class UserRegister(User):
    password: str = None


class UserInDB(UserInfo):
    hashed_password: str


class UserUpdate(User):
    password: Optional[str] = None
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None


class UserDatabaseScheme(UserInfo):
    hashed_password: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Usage(BaseModel):
    created_at: datetime
    status_code: int
    id: Optional[int] = None
    email: str

    class Config:
        orm_mode = True

class UsageCount(BaseModel):
    total_count: int
    success_count: int
    failed_count: int

