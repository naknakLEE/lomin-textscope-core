from typing import Any, Dict, List
from itertools import cycle
from fastapi import Depends, APIRouter, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.database.schema import Usage, Users, UserUpdate
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app.common.const import get_settings
from app import models


settings = get_settings()
router = APIRouter()


@router.get("/users", response_model=List[models.UserInfo])
def read_users(
    session: Session = Depends(db.session),
    skip: int = 0,
    limit: int = 100,
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    skip 부터 limit 만큼의 유저 정보 조회
    """
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    users = Users.get_multi(session, skip=skip, limit=limit)
    return users


@router.post("/users/create", response_model=models.UserInfo)
def create_user(
    *,
    session: Session = Depends(db.session),
    user: models.UserRegister,
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    새로운 유저 생성
    """
    user = user.__dict__
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user["email"])
    is_exist = Users.get(session, email=user["email"])
    if is_exist:
        raise ex.AlreadyExistException(user["email"])
    user["hashed_password"] = get_password_hash(user["password"])
    created_user = Users.create(session, auto_commit=True, **user)
    return created_user


@router.get("/users/{user_email}", response_model=models.UserInfo)
def read_user_by_email(
    user_email: EmailStr,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    특정한 유저 정보 조회
    """
    user = Users.get(session, email=user_email)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    return user


@router.put("/users/{user_email}", response_model=models.UserInfo)
def update_user(
    *,
    session: Session = Depends(db.session),
    user_email: EmailStr,
    user_in: UserUpdate,
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    특정한 유저 정보 업데이트
    """
    user = Users.get(session, email=user_email)
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    if not user:
        raise ex.AlreadyExistException(current_user.email)

    hashed_password = get_password_hash(user_in.password)
    user_in = models.UserDatabaseScheme(
        **user_in.__dict__, hashed_password=hashed_password
    )
    user = Users.update(session, db_obj=user, obj_in=user_in)
    return user


@router.get("/inference/usage", response_model=List[models.Usage])
def read_usage(
    skip: int = 0,
    limit: int = 100,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    전체 유저의 요청 정보 조회
    """
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage(session, skip=skip, limit=limit)
    return usages


@router.get("/inference/usage/{user_email}", response_model=List[models.Usage])
def read_usage_by_email(
    user_email: EmailStr,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    특정한 유저의 요청 정보 조회
    """
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage(session, email=user_email)
    return usages


@router.get("/inference/count", response_model=models.UsageCount)
def count_usage(
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    전체 유저의 사용량 조회
    """
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage_count(session)
    return cal_usage_count(usages)


@router.get("/inference/count/{user_email}", response_model=models.UsageCount)
def count_usage_by_email(
    user_email: EmailStr,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    특정한 유저의 사용량 조회
    """
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage_count(session, email=user_email)
    return cal_usage_count(usages)


def cal_usage_count(usages) -> Dict:
    successed_count = (
        sum(usages["success_response"][0]) if len(usages["success_response"]) else 0
    )
    failed_count = (
        sum(usages["failed_response"][0]) if len(usages["failed_response"]) else 0
    )
    return {
        "total_count": successed_count + failed_count,
        "success_count": successed_count,
        "failed_count": failed_count,
    }
