from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import Depends, APIRouter, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.common.const import get_settings
from app.schemas.json_schema import admin_users_responses
from starlette.responses import JSONResponse
from app.middlewares.exception_handler import CoreCustomException
from app.utils.utils import is_admin, get_ts_uuid, get_company_group_prefix
from fastapi.encoders import jsonable_encoder



from app import models
from app.database import query, schema



settings = get_settings()
router = APIRouter()


@router.get(
    "/template")
def get_rpa_template(
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### rpa 템플릿 조회
    관리자가 아니면 조회 불가능
    """
        
    # emp_usr_emad=current_user.email인 사원의 정보
    request_company_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_company_user_info, JSONResponse):
        raise CoreCustomException(2509)
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 관리자가 아닐경우 에러 응답 반환
    if not is_admin(user_policy_result):
        raise CoreCustomException(2509)
    
    latest_rpa_template = query.select_rpa_form_info_get_all_latest(session)
    response = dict(
        receiver_email = latest_rpa_template.rpa_receiver_email,
        email_title = latest_rpa_template.rpa_title,
        email_body = latest_rpa_template.rpa_body,
        nas_path = latest_rpa_template.rpa_nas_path
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.post(
    "/template")
def post_rpa_template(
    params: dict = Body(...),
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### rpa 템플릿 수정
    관리자가 아니면 수정 불가능
    """
        
    receiver_email:  str  = params.get("receiver_email")
    email_title:     str  = params.get("email_title")
    email_body:      str  = params.get("email_body")
    nas_path:        str  = params.get("nas_path")
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_company_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_company_user_info, JSONResponse):
        raise CoreCustomException(2509)
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 관리자가 아닐경우 에러 응답 반환
    if not is_admin(user_policy_result):
        raise CoreCustomException(2509)
    
    insert_rpa_form_info_result = query.insert_rpa_form_info(
        session,
        rpa_receiver_email = receiver_email,
        rpa_title = email_title,
        rpa_body = email_body,
        rpa_nas_path = nas_path,
        rpa_created_owner = current_user.email
    )
    del insert_rpa_form_info_result
    
    response = dict(
        status="success"
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))
    
    
