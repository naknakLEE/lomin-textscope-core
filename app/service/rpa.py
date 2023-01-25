from typing import Any
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.config import hydra_cfg
from app.utils.rpa import send_rpa_only_cls_FN
from starlette.responses import JSONResponse
from app.middlewares.exception_handler import CoreCustomException
from app.utils.utils import is_admin
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials


from app import models
from app.database import query


def get_rpa_template(
    session: Session,
    current_user: models.UserInfo,
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

def post_rpa_template(
    params: dict,
    session: Session,
    current_user: models.UserInfo,
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

async def post_rpa(
    params: dict,
    session: Session,
    background_tasks: BackgroundTasks,
    current_user: models.UserInfo,
    token: HTTPAuthorizationCredentials,
) -> Any:
    """
    ### RPA 전송을 수동으로 진행합니다.
    
    문서 종류 해외 투자 신고서류에 한에서만 RPA 전송이 이루어집니다.
    
    해외 투자 신고서류 이외의 파일이 들어오면 RPA 전송을 진행하지 않습니다.
    
    """
        
    document_id:  str  = params.get("document_id")
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_company_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_company_user_info, JSONResponse):
        raise CoreCustomException(2509)
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    user_policy_result: dict = user_policy_result
    
    # 관리자가 아닐경우 에러 응답 반환
    if not is_admin(user_policy_result):
        raise CoreCustomException(2509)
    
    status = "fail, rpa.use = False"
    
    if hydra_cfg.common.rpa.use:
        background_tasks.add_task(
            send_rpa_only_cls_FN,
            session=session,
            user_email=current_user.email,
            document_id=document_id,
            token=token
        )
        
        status = "success"
    
    
    response = dict(
        status=status
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response), background=background_tasks)    