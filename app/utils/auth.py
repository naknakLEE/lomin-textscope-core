from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.param_functions import Form
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.schema import Users
from app.models import TokenData, User, UserInDB, Token
from app.common.const import get_settings
from app.errors import exceptions as ex


settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(email: EmailStr):
    is_exist = is_email_exist(email)
    if is_exist:
        user = Users.get(email=email)
        user_dict = {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "hashed_password": user.hashed_password,
        }
        return UserInDB(**user_dict)


def is_username_exist(username: str):
    get_username = Users.get(username=username)
    if get_username:
        return True
    return False


def is_email_exist(email: EmailStr):
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def authenticate_user(email: EmailStr, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# async def get_current_user(token: str = Depends(oauth2_scheme)):
async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise ex.InvalidCredentiolException(username)
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise ex.JWTExpiredExetpion()
    except JWTError:
        raise ex.JWTException(JWTError)
    user = get_user(email=token_data.username)
    if user is None:
        raise ex.NotFoundUserException(username)
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


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
