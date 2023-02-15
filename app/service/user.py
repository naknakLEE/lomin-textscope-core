from datetime import datetime
from typing import Any, Optional, List, Dict
from fastapi import Depends, APIRouter, Body
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr
import urllib.parse

from app.common.const import settings
from app.database.connection import db
# from app.database.schema import Users, Usage
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app.schemas.json_schema import users_me_responses
from app import models
from app.models import UserInfo as UserInfoInModel
from app.schemas import error_models as ErrorResponse

from app.database import query, schema
from app.utils.utils import is_admin
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



def get_user_info_by_user_email(
    user_email:   str,
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:
    
    user_email = urllib.parse.unquote(user_email)
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_user_info, JSONResponse):
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    request_user_info: schema.CompanyUserInfo = request_user_info
    request_company_info: schema.CompanyInfo = request_user_info.company_info
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 자신이 아닌 다른 사원의 정보를 조회하는데 관리자가 아닐경우 에러 응답 반환
    if user_email != current_user.email and not is_admin(user_policy_result):
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # emp_usr_emad=user_email인 사원의 정보
    company_user_info = query.select_company_user_info(session, emp_usr_emad=user_email)
    if isinstance(company_user_info, JSONResponse):
        return company_user_info
    company_user_info: schema.CompanyUserInfo = company_user_info
    company_info: schema.CompanyInfo = company_user_info.company_info
    
    # 해당 사원의 회사가 current_user.email의 회사와 다르면 에러 응답 반환
    if company_info.company_code != request_company_info.company_code:
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    
    response = dict(
        user_info = dict(
            company_code  = str(company_info.company_code),
            company_name  = str(company_info.company_name),
            
            user_eno      = str(company_user_info.emp_eno),
            user_nm       = str(company_user_info.emp_usr_nm),
            user_email    = str(company_user_info.emp_usr_emad),
            user_ph       = str(company_user_info.emp_usr_mpno),
            user_tno      = str(company_user_info.emp_inbk_tno),
            
            user_decd     = str(company_user_info.emp_decd),
            user_tecd     = str(company_user_info.emp_tecd),
            user_org_path = str(company_user_info.emp_org_path),
            user_ofps_cd  = str(company_user_info.emp_ofps_cd),
            user_ofps_nm  = str(company_user_info.emp_ofps_nm)
        )
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))
