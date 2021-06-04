from datetime import datetime
from typing import Optional
from jose.utils import int_arr_to_long
from pydantic.main import BaseModel
from pydantic.networks import EmailStr


class UserRegister(BaseModel):
    email: EmailStr = None
    password: str = None


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
    id: Optional[int] = None
    username: Optional[str]
    email: EmailStr = None
    full_name: Optional[str] = None
    disabled: bool = False
    is_active: Optional[bool] = None
    is_superuser: bool = False

    class  Config:
        orm_mode = True


class UserInDB(User):
    hashed_password: str


class UserUpdate(User):
    hashed_password: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Usage(BaseModel):
    created_at: datetime
    status_code: int
    id: Optional[int] = None
    email: EmailStr

    class Config:
        orm_mode = True

class UsageCount(BaseModel):
    total_count: int
    success_count: int
    failed_count: int
