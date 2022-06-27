import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Body
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.utils.utils import get_ts_uuid
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.utils.document import (
    get_page_count,
    is_support_format,
    save_upload_document,
)
from app.utils.image import (
    get_crop_image,
    get_image_info_from_bytes,
    get_image_bytes,
    load_image,
)
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



settings = get_settings()
router = APIRouter()



@router.post("/save")
def post_inspect_info(
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    검수 정보 임시 저장 및 저장
    TODO 에러응답 추가
        inspect_date_startㅣ 없을때
        inspect_done True인데 inpsect_end_time이 없을때
    """
    user_email = params.get("user_email", current_user.email)
    document_id = params.get("document_id")
    page_num = params.get("page_num", 0)
    inspect_date_start = params.get("inspect_date_start")
    inspect_date_end = params.get("inspect_date_end")
    inspect_result = params.get("inspect_result", {})
    inspect_accuracy = params.get("inspect_accuracy", 0.0)
    inspect_done = params.get("inspect_done", False)
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 자신의 권한(그룹, 역할) 정보 조회
    # 슈퍼어드민(0) 또는 관리자(1)이 아닐경우 검수 제한
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    
    # 슈퍼어드민 또는 관리자가 아닌데 다른 부서의 문서를 검수 한다면 오류 반환
    if is_admin is False and select_document_result.user_team != user_team:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 검수 결과 저장 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # document_id로 특정 페이지의 가장 최근 inference info.inference_id 조회
    select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
    if isinstance(select_inference_result, JSONResponse):
        return select_inference_result
    select_inference_result: schema.InferenceInfo = select_inference_result
    inference_id = select_inference_result.inference_id
    
    # inference_id에 해당하는 추론에 대한 검수 결과 저장
    inspect_id = get_ts_uuid("inpsect")
    inspect_status = settings.INSPECT_STATUS_SUSPEND
    if inspect_done is True:
        inspect_status = settings.INSPECT_STATUS_COMPLET
        inspect_date_end = inspect_date_end if inspect_date_end else datetime.now()
    else:
        inspect_date_end = None
    insert_inspect_result = query.insert_inspect(
        session,
        inspect_id=inspect_id,
        user_email=user_email,
        user_team=user_team,
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
    
    # 가장 최근 검수 정보 업데이트
    update_document_result = query.update_document(
        session,
        document_id,
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
