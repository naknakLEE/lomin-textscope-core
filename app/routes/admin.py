from datetime import datetime
from typing import Any, List, Optional
from fastapi import Depends, APIRouter, Body
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.common.const import get_settings
from app.schemas.json_schema import admin_users_responses
from app import models
from app.service.admin import (
    read_users,
    create_user,
    read_user_by_email,
    update_user,
    read_usage,
    read_usage_by_email,
    count_usage,
    count_usage_by_email
)

settings = get_settings()
router = APIRouter()


@router.get(
    "/users", response_model=List[models.UserInfo], responses=admin_users_responses
)
def read_users(
    session: Session = Depends(db.session),
    skip: int = 0,
    limit: int = 100,
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### 유저 정보를 조회
    한번에 여러 유저의 정보를 조회 가능하도록 구성 <br/>
    skip으로 offset을 설정하며, limit 수만큼의 유저 정보 조회
    """
    return read_users(
        session = session,
        current_user = current_user,
        skip = skip,
        limit = limit
    )


@router.post(
    "/users/create", response_model=models.UserInfo, responses=admin_users_responses
)
def create_user(
    *,
    session: Session = Depends(db.session),
    user: models.UserRegister = Body(..., example=models.UserInfo.schema()["example"]),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### 데이터베이스에 새로운 유저 생성
    유저가 생성 과정 진행 후 생성된 유저 정보 반환 <br/>
    반환된 유저 정보에는 입력 받은 정보 외에도 계정 활성화 상태 (disabled), 현재 활동 여부 (is_active), superuser 권한을 소유하고 있는지 (is_superuser), id에 대한 정보 포함
    """
    return create_user(
        session = session,
        user = user,
        current_user = current_user
    )


@router.get(
    "/users/{user_email}",
    response_model=models.UserInfo,
    responses=admin_users_responses,
)
def read_user_by_email(
    user_email: EmailStr,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 특정한 유저 정보 조회
    반환된 유저 정보에는 email, username, full_name, 계정 활성화 상태 (disabled), 현재 활동 여부 (is_active), superuser 권한을 소유하고 있는지 (is_superuser), id가 몇 번인지 (id)에 대한 정보 포함
    """
    
    return read_user_by_email(
        user_email = user_email,
        current_user = current_user,
        session = session
    )


@router.put(
    "/users/{user_email}",
    response_model=models.UserInfo,
    responses=admin_users_responses,
)
def update_user(
    *,
    session: Session = Depends(db.session),
    user_in: models.UserUpdate = Body(..., example=models.UserUpdate.schema()["example"]),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
        ### 특정한 유저 정보 업데이트
        email, username, full_name, 계정 활성화 상태 (disabled), 현재 활동 여부 (is_active), superuser 권한을 소유하고 있는지 (is_superuser), id에 대한 정보 중에 입력한 부분 업데이트
    """
    return update_user(
        session = session,
        user_in = user_in,
        current_user = current_user
    )


@router.get("/usage/inference", response_model=List[models.Usage])
def read_usage(
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
        ### 전체 유저의 사용량 정보 조회
        skip으로 offset을 설정하며, limit 수만큼의 사용량 정보 조회 <br/>
        해당 호출에서 각 요청에 대한 정보에는 요청 일시, 상태 코드, 이메일 포함
    """
    return read_usage(
        start_time = start_time,
        end_time = end_time,
        current_user = current_user,
        session = session,
        skip = skip,
        limit = limit
    )


@router.get("/usage/inference/{user_email}", response_model=List[models.Usage])
def read_usage_by_email(
    user_email: EmailStr,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 특정한 유저의 요청 정보 조회
    해당 호출의 응답은 특정한 유저의 각 요청에 대한 정보에는 요청 일시, 상태 코드, 이메일가 포함
    """
    return read_usage_by_email(
        user_email = user_email,
        start_time = start_time,
        end_time = end_time,
        current_user = current_user,
        session = session
    )


@router.get("/count/inference", response_model=models.UsageCount)
def count_usage(
    current_user: models.UserInfo = Depends(get_current_active_user),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 전체 유저의 사용량 조회
    해당 호출은 총 요청 수, 성공한 요청 수, 실패한 요청 수를 반환
    """
    return count_usage(
        current_user = current_user,
        start_time = start_time,
        end_time = end_time,
        session = session
    )


@router.get("/count/inference/{user_email}", response_model=models.UsageCount)
def count_usage_by_email(
    user_email: EmailStr,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.UserInfo = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 특정한 유저의 사용량 조회
    해당 호출은 특정한 유저의 총 요청 수, 성공한 요청 수, 실패한 요청 수를 반환
    """
    return count_usage_by_email(
        user_email = user_email,
        start_time = start_time,
        end_time = end_time,
        current_user = current_user,
        session = session
        )

