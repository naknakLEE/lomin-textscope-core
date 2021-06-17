from datetime import datetime, timedelta
from typing import Optional, Any
import time

from fastapi import Depends, HTTPException, status, Security
from fastapi.param_functions import Form
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic.networks import EmailStr
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.schema import Users
from app.models import TokenData, User, UserInDB
from app.common.const import get_settings
from app.errors import exceptions as ex
from app.database.connection import db


settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="asdfg/token",
#     scopes={"me": "Read information about the current user.", "items": "Read items."},
# )


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def get_user(email: EmailStr, session: Session) -> UserInDB:
    user = is_email_exist(email, session)
    if user:
        user_dict = {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "hashed_password": user.hashed_password,
        }
        return UserInDB(**user_dict)


def is_username_exist(username: str, session: Session) -> Any:
    user = Users.get(session=session, username=username)
    if user:
        return user
    return False


def is_email_exist(email: EmailStr, session: Session) -> Any:
    user = Users.get(session=session, email=email)
    if user:
        return user
    return False


def authenticate_user(email: EmailStr, password: str, session: Session) -> Any:
    user = get_user(email, session)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        print("\n\n\n check", user)
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# async def get_current_user(token: str = Depends(oauth2_scheme)):
# token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
async def get_current_user(
    security_scopes: SecurityScopes,
    token: HTTPAuthorizationCredentials = Security(security),
    session=Depends(db.session),
) -> Any:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"

    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise ex.InvalidCredentiolException(email)
        # token_data = TokenData(email=email)
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, email=email)

    except ExpiredSignatureError:
        raise ex.JWTExpiredExetpion()
    except (JWTError, ValidationError):
        raise ex.JWTException(JWTError)

    user = get_user(email=token_data.email, session=session)
    if user is None:
        raise ex.JWTNotFoundUserException(email)
    print("\033[96m" + f"{token_data}" + "\033[m")
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise ex.JWTScopeException(authenticate_value)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
