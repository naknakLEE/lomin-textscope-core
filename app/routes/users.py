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


@router.get("/me", response_model=models.User)
async def read_users_me(current_user: dict = Depends(get_current_active_user)) -> Any:
    """
    현재 유저 정보 조회
    """
    return current_user


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
    현재 유저 정보 업데이트
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
