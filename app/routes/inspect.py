from datetime import datetime
from typing import List, Dict

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
from app.utils.utils import get_ts_uuid, is_admin, get_company_group_prefix
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.utils.inspect import get_inspect_accuracy, get_inspect_accuracy_avg
from app.middlewares.exception_handler import CoreCustomException
from app.utils.inspect import is_doc_type_in_cls_group
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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 사용자 정책(조회 가능 문서 종류(대분류)) 확인
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_idx_list_result = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_idx_list_result, JSONResponse):
        return cls_type_idx_list_result
    
    cls_type_idx_result_list: Dict[int, dict] = { x.get("index") : x for x in cls_type_idx_list_result }
    cls_type_doc_type_list: Dict[int, List[int]] = { cls_type : [ x.get("index") for x in doc_type.get("docx_type", []) ] for cls_type, doc_type in cls_type_idx_result_list.items() }
    
    # 사용자 정책(조회 가능 문서 종류(소분류)) 확인
    doc_type_idx_code: Dict[int, dict] = dict()
    for cls_type_info in cls_type_idx_result_list.values():
        for doc_type_info in cls_type_info.get("docx_type", []):
            doc_type_idx_code.update({doc_type_info.get("index"):doc_type_info})
    
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
        
        # 문서 종류(대분류)와 종류(소분류)가 맞지 않거나, 권한 없는 문서 종류(소분류)이거나, 일반서류일때 인식률 None
        if select_inference_result.doc_type_idx not in cls_type_doc_type_list.get(select_document_result.cls_idx, []) \
            or select_inference_result.doc_type_idx not in doc_type_idx_code.keys() \
            or select_inference_result.doc_type_idx in [0, 31]:
            inspect_accuracy = None
        else:
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
