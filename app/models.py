from typing import Optional
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
    username: Optional[str] = None


class User(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class UserUpdate(User):
    hashed_password: Optional[str] = None
