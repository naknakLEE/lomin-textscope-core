from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import db
from app.models import UserInfo as UserInfoInModel
from app.config import hydra_cfg
from app.service.user import (
    get_user_info_by_user_email as get_user_info_by_user_email_service,
    post_user_policy as post_user_policy_service,
    get_all_policy_log as get_all_policy_log_service,
    get_company_users_authority as get_company_users_authority_service,
)
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user

router = APIRouter()


# 이메일 정보로 "사원정보" 조회
@router.get("/{user_email}")
def get_user_info_by_user_email(
    user_email:   str,
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:
        
    return get_user_info_by_user_email_service(
        user_email = user_email,
        session = session,
        current_user = current_user
    )


@router.post("/{user_email}/authority")
def post_user_policy(
    user_email:str,
    authority: str,
    authority_time_start: str,
    authority_time_end:   str,
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:
    
    return post_user_policy_service(
        user_email=user_email,
        authority=authority,
        authority_time_start=authority_time_start,
        authority_time_end=authority_time_end,
        session=session,
        current_user=current_user
    )


@router.post("/authority/log")
def get_all_policy_log(
    authority_date_start: str,
    authority_date_end:   str,
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:

    return get_all_policy_log_service(
        authority_date_start=authority_date_start,
        authority_date_end=authority_date_end,
        session=session,
        current_user=current_user
    )

# "사원"정보 조회
@router.get("/authority/list")
def get_company_users_authority(
    search_text:  str,
    rows_limit:   int,
    rows_offset:  int,
    filter_authority: str = "관리자일반없음",
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:

    return get_company_users_authority_service(
        search_text=search_text,
        rows_limit=rows_limit,
        rows_offset=rows_offset,
        filter_authority=filter_authority,
        session=session,
        current_user=current_user
    )