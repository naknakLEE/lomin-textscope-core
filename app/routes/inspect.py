from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Body, Request, Security
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.utils.rpa import send_rpa_only_cls_FN
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.utils.utils import get_ts_uuid, is_admin
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.utils.inspect import get_inspect_accuracy, get_inspect_accuracy_avg
from app.middlewares.exception_handler import CoreCustomException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


security = HTTPBearer()
settings = get_settings()
router = APIRouter()


@router.post("/save")
async def post_inspect_info(
    request: Request,
    params: dict = Body(...),
    token: HTTPAuthorizationCredentials = Security(security),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    검수 정보 임시 저장 및 저장
    TODO 에러응답 추가
        inspect_date_startㅣ 없을때
        inspect_done True인데 inpsect_end_time이 없을때
    """
    user_email:         str   = current_user.email
    document_id:        str   = params.get("document_id")
    page_num:           int   = params.get("page_num", 0)
    inspect_date_start: str   = params.get("inspect_date_start", datetime.now())
    inspect_date_end:   str   = params.get("inspect_date_end")
    inspect_result:     dict  = params.get("inspect_result")
    inspect_accuracy:   float = params.get("inspect_accuracy", 0.0)
    inspect_done:       bool  = params.get("inspect_done", False)
    
    # 사용자 정보 조회
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 문서 상태가 RUNNING_INFERENCE면 에러 응답 반환
    if select_document_result.inspect_id == "RUNNING_INFERENCE":
        raise CoreCustomException(2513)
    
    # 문서에 대한 권한이 없을 경우 에러 응답 반환
    if select_document_result.user_team not in user_team_list:
        raise CoreCustomException(2505)
    
    # 검수 중인데 자신의 검수 중인 문서가 아니거나 관리자가 아닐 경우 에러 응답 반환
    inspect_id = select_document_result.inspect_id
    select_inspect_result = query.select_inspect_latest(session, inspect_id=inspect_id)
    if isinstance(select_inspect_result, JSONResponse):
        return select_inspect_result
    select_inspect_result: schema.InspectInfo = select_inspect_result
    if select_inspect_result.inspect_status == settings.STATUS_INSPECTING:
        if not is_admin(user_policy_result) and select_inspect_result.user_email != user_email:
            raise CoreCustomException(2511)
    
    # 검수 결과 저장 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # document_id로 특정 페이지의 가장 최근 inference info.inference_id 조회
    select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
    if isinstance(select_inference_result, JSONResponse):
        return select_inference_result
    select_inference_result: schema.InferenceInfo = select_inference_result
    inference_id = select_inference_result.inference_id
    
    # inference_id에 해당하는 추론에 대한 검수 결과 저장
    inspect_id = get_ts_uuid("inpsect")
    inspect_status = settings.STATUS_INSPECTING
    if inspect_done is True:
        inspect_status = settings.STATUS_INSPECTED
        inspect_date_end = inspect_date_end if inspect_date_end else datetime.now()
        
        if hydra_cfg.common.rpa.use: # rpa 시작
            try:
                await send_rpa_only_cls_FN(session, user_email, document_id, token)
            except Exception as ex:
                logger.error(f"RPA 전송 실패 : error code: {ex.error.error_code} msg : {ex.error.error_message}")
        
        # 인식률 확인
        inspect_accuracy = get_inspect_accuracy(session, select_inference_result, inspect_result)
        
    else:
        inspect_date_end = None
        inspect_accuracy = None
    
    insert_inspect_result = query.insert_inspect(
        session,
        auto_commit=True,
        inspect_id=inspect_id,
        user_email=user_email,
        user_team=select_user_result.user_team,
        inference_id=inference_id,
        inspect_start_time=inspect_date_start,
        inspect_end_time=inspect_date_end,
        inspect_result=inspect_result,
        inspect_accuracy=inspect_accuracy,
        inspect_status=inspect_status
    )
    if isinstance(insert_inspect_result, JSONResponse):
        return insert_inspect_result
    del insert_inspect_result
    
    inspect_accuracy_avg = None
    if inspect_status == settings.STATUS_INSPECTED:
        # 문서 평균 정확도
        inspect_accuracy_avg = get_inspect_accuracy_avg(session, select_document_result)
    
    # 가장 최근 검수 정보, 문서 평균 정확도 업데이트
    update_document_result = query.update_document(
        session,
        document_id,
        document_accuracy=inspect_accuracy_avg,
        inspect_id=inspect_id
    )
    if isinstance(update_document_result, JSONResponse):
        return update_document_result
    del update_document_result
    
    
    response = dict(
        resource_id=dict(
            inspect_id=inspect_id
        )
    )
    
    return JSONResponse(status_code=201, content=jsonable_encoder(response))
