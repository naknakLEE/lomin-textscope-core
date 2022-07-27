from datetime import datetime
from typing import Any, Optional, List, Dict
from fastapi import Depends, APIRouter, Body
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr
import urllib.parse

from app.database.connection import db
# from app.database.schema import Users, Usage
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app.schemas.json_schema import users_me_responses
from app import models
from app.models import UserInfo as UserInfoInModel
from app.schemas import error_models as ErrorResponse

from app import hydra_cfg
from app.database import query, schema
from app.utils.utils import is_admin
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user

router = APIRouter()


# 이메일 정보로 사원정보 조회
@router.get("/{user_email}")
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
    admin = is_admin(user_policy_result)
    if user_email != current_user.email and not admin:
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
            
            user_rgst_t   = str(company_user_info.emp_fst_rgst_dttm),
            user_eno      = str(company_user_info.emp_eno),
            user_nm       = str(company_user_info.emp_usr_nm),
            user_email    = str(company_user_info.emp_usr_emad),
            user_ph       = str(company_user_info.emp_usr_mpno),
            user_tno      = str(company_user_info.emp_inbk_tno),
            
            user_decd     = str(company_user_info.emp_decd),
            user_tecd     = str(company_user_info.emp_tecd),
            user_org_path = str(company_user_info.emp_org_path),
            user_ofps_cd  = str(company_user_info.emp_ofps_cd),
            user_ofps_nm  = str(company_user_info.emp_ofps_nm),
            admin         = str(admin)
        )
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


# @router.get("/me", response_model=models.UserInfo, responses=users_me_responses)
# async def read_users_me(
#     session: Session = Depends(db.session),
#     current_user: dict = Depends(get_current_active_user),
# ) -> Any:
#     """
#     ### 토큰 생성시 입력했던 이메일 조회
#     입력 데이터: 이메일 정보 조회할 토큰 <br/>
#     응답 데이터: 토큰 생성시 입력한 이메일 정보
#     """
#     user_info = Users.get_by_email(session, email=current_user.email)
#     print("\033[95m" + f"{user_info.__dict__}" + "\033[m")
#     return user_info


# @router.put("/me", response_model=models.UserInfo, responses=users_me_responses)
# def update_user_me(
#     *,
#     session: Session = Depends(db.session),
#     user_in: models.UserRegister = Body(
#         ..., example=models.UserInfo.schema()["example"]
#     ),
#     current_user: models.UserInfo = Depends(get_current_active_user),
# ) -> Any:
#     """
#     ### 현재 유저 정보 업데이트
#     입력 데이터: 토큰 발급받은 유저의 email, full_name, username, password 중 변경할 데이터 <br/>
#     응답 데이터: 업데이트된 유저 정보 반환

#     """
#     user_in = models.UserInDB(**user_in.__dict__)
#     user = Users.get(session, email=user_in.email)
#     user_in.id = user.id
#     if user_in.password is not None:
#         user_in.hashed_password = get_password_hash(user_in.password)
#     updated_user = Users.update(session, **vars(user_in))
#     return updated_user


# @router.get("/usage/me", response_model=List[models.Usage])
# def read_usage_me_by_email(
#     start_time: Optional[datetime] = None,
#     end_time: Optional[datetime] = None,
#     current_user: models.User = Depends(get_current_active_user),
#     session: Session = Depends(db.session),
# ) -> Any:
#     """
#     ### 현재 유저의 사용량 정보 조회
#     입력 데이터: 사용량 정보를 조회할 유저의 토큰 <br/>
#     응답 데이터: 사용량 정보 배열 (각 ocr 요청에 대한 사용일, 상태코드, 이메일 정보 포함)
#     """
#     usages = Usage.get_usage(
#         session, email=current_user.email, start_time=start_time, end_time=end_time
#     )
#     return usages


# @router.get("/count/me", response_model=models.UsageCount)
# def count_usage_me(
#     start_time: Optional[datetime] = None,
#     end_time: Optional[datetime] = None,
#     current_user: models.User = Depends(get_current_active_user),
#     session: Session = Depends(db.session),
# ) -> Any:
#     """
#     ### 현재 유저의 사용량 조회
#     입력 데이터: 사용량 조회할 유저의 토큰 <br/>
#     응답 데이터: ocr 시도 횟수, ocr 성공 횟수, ocr 실패 횟수
#     """
#     usages = Usage.get_usage_count(
#         session, email=current_user.email, start_time=start_time, end_time=end_time
#     )
#     return cal_usage_count(usages)


# def cal_usage_count(usages) -> Dict:
#     successed_count = (
#         sum(usages["success_response"][0]) if len(usages["success_response"]) else 0
#     )
#     failed_count = (
#         sum(usages["failed_response"][0]) if len(usages["failed_response"]) else 0
#     )
#     return {
#         "total_count": successed_count + failed_count,
#         "success_count": successed_count,
#         "failed_count": failed_count,
#     }
