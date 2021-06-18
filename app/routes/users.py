from typing import Any

from fastapi import Depends, APIRouter
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.database.schema import Users, UserUpdate
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app import models


router = APIRouter()


@router.get("/me", response_model=EmailStr)
async def read_users_me(current_user: dict = Depends(get_current_active_user)) -> Any:
    """
    ### 토큰 생성시 입력했던 이메일 조회
    입력 데이터: 이메일 정보 조회할 토큰 <br/>
    응답 데이터: 토큰 생성시 입력한 이메일 정보
    """
    return current_user.email


@router.put("/me", response_model=models.UserInfo)
def update_user_me(
    session: Session = Depends(db.session),
    email: EmailStr = None,
    full_name: str = None,
    username: str = None,
    password: str = None,
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### 현재 유저 정보 업데이트
    입력 데이터: 토큰 발급받은 유저의 email, full_name, username, password 중 변경할 데이터 <br/>
    응답 데이터: 업데이트된 유저 정보 반환
    
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if password is not None:
        user_in.hashed_password = get_password_hash(password)
    if full_name is not None:
        user_in.full_name = full_name
    if username is not None:
        user_in.username = username
    if email is not None:
        user_in.email = email
    updated_user = Users.update(session, db_obj=current_user, obj_in=user_in)
    return updated_user
