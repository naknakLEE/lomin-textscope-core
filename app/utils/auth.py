from datetime import datetime, timedelta
from typing import Optional

from ldap3 import Server, ALL
from fastapi import Depends, HTTPException, Security
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic.networks import EmailStr
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.schema import UserInfo as UserInfoInDB
from app.models import TokenData
from app.models import UserInfo as UserInfoInModel
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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(email: EmailStr, session: Session) -> Optional[UserInfoInModel]:
    user = is_email_exist(email, session)
    if user:
        user_dict = {
            "employee_num": user.user_employee_num,
            "email": user.user_email,
            "password": user.user_pw,
            "office": user.user_office,
            "division": user.user_division,
            "department": user.user_department,
            "team": user.user_team,
            "name": user.user_name,
            "status": "active" if user.is_used else "disabled"
        }
        return UserInfoInModel(**user_dict)
    return None


def is_email_exist(email: EmailStr, session: Session) -> Optional[UserInfoInDB]:
    user = UserInfoInDB.get(session=session, user_email=email)
    if user:
        return user
    return None


def authenticate_user(
    email: EmailStr, password: str, session: Session
) -> Optional[UserInfoInDB]:
    user = get_user(email, session)
    if user:
        if user.password is None:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
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
    session: Session = Depends(db.session),
) -> UserInfoInModel:
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
            raise ex.JWTScopeException(authenticate_value=authenticate_value)
    return user


async def get_current_active_user(
    current_user: UserInfoInModel = Depends(get_current_user),
) -> UserInfoInModel:
    if current_user.status == "disabled":
        raise HTTPException(status_code=400, detail="Disabled user")
    return current_user


async def initialize_ldap() -> Server:
    server = Server("LDAP://openldap:389", get_info=ALL)
    return server

def get_current_active_user_fake():
    pass