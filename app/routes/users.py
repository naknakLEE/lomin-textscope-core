from datetime import datetime
from typing import Any, Optional, List, Dict
from fastapi import Depends, APIRouter, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.database.schema import Users, Usage
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app.schemas import users_me_responses
from app import models


router = APIRouter()


@router.get("/me", response_model=models.UserInfo, responses=users_me_responses)
async def read_users_me(
    session: Session = Depends(db.session),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    ### 토큰 생성시 입력했던 이메일 조회
    입력 데이터: 이메일 정보 조회할 토큰 <br/>
    응답 데이터: 토큰 생성시 입력한 이메일 정보
    """
    user_info = Users.get_by_email(session, email=current_user.email)
    print("\033[95m" + f"{user_info.__dict__}" + "\033[m")
    return user_info


@router.put("/me", response_model=models.UserInfo, responses=users_me_responses)
def update_user_me(
    *,
    session: Session = Depends(db.session),
    user_in: models.UserRegister = Body(
        ..., example=models.UserInfo.schema()["example"]
    ),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### 현재 유저 정보 업데이트
    입력 데이터: 토큰 발급받은 유저의 email, full_name, username, password 중 변경할 데이터 <br/>
    응답 데이터: 업데이트된 유저 정보 반환

    """
    # current_user_data = jsonable_encoder(current_user)
    user_in = models.UserInDB(**user_in.__dict__)
    if user_in.password is not None:
        user_in.hashed_password = get_password_hash(user_in.password)
    if user_in.full_name is not None:
        user_in.full_name = user_in.full_name
    if user_in.username is not None:
        user_in.username = user_in.username
    if user_in.email is not None:
        user_in.email = user_in.email
    updated_user = Users.update(session, db_obj=current_user, obj_in=user_in)
    return updated_user


@router.get("/usage/me", response_model=List[models.Usage])
def read_usage_me_by_email(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 현재 유저의 사용량 정보 조회
    입력 데이터: 사용량 정보를 조회할 유저의 토큰 <br/>
    응답 데이터: 사용량 정보 배열 (각 ocr 요청에 대한 사용일, 상태코드, 이메일 정보 포함)
    """
    usages = Usage.get_usage(
        session, email=current_user.email, start_time=start_time, end_time=end_time
    )
    return usages


@router.get("/count/me", response_model=models.UsageCount)
def count_usage_me(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    ### 현재 유저의 사용량 조회
    입력 데이터: 사용량 조회할 유저의 토큰 <br/>
    응답 데이터: ocr 시도 횟수, ocr 성공 횟수, ocr 실패 횟수
    """
    usages = Usage.get_usage_count(
        session, email=current_user.email, start_time=start_time, end_time=end_time
    )
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
