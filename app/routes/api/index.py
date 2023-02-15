import os
import requests  # type: ignore

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi import BackgroundTasks
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import base64

from app.utils.background import bg_ocr
from app.database.connection import db
from app.database import query, schema
from app.models import UserInfo as UserInfoInModel
from app.common.const import settings
from app.utils.logging import logger
from app import models
from app.utils.document import document_path_verify
from app.utils.utils import cal_time_elapsed_seconds, get_ts_uuid
from app.schemas import error_models as ErrorResponse
from app.schemas import HTTPBearerFake
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
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


@router.post("/docx")
async def post_upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    params: dict = Body(...), 
    session: Session = Depends(db.session),
) -> JSONResponse:
    
    response: dict = dict(resource_id=dict())
    response_log: dict = dict()
    request_datetime = datetime.now()
    
    user_email:            str = current_user.email
    document_id:          str = params.get("document_id", get_ts_uuid("document"))
    document_name:        str = params.get("file_name")
    document_data:        str = params.get("file")
    document_description: str = params.get("description")
    document_type:        str = params.get("document_type")
    document_path:        str = params.get("document_path")
    
    # document_data가 없고 document_path로 요청이 왔는지 확인
    # document_path로 왔으면 파일 읽기
    if document_data is None and document_path is not None:
        file_path = Path(document_path)
        document_name = file_path.name
        path_verify = document_path_verify(document_path)
        if isinstance(path_verify, JSONResponse): return path_verify
        
        with file_path.open('rb') as file:
            document_data = await file.read()
        document_data = base64.b64encode(document_data)
    
    # 유저 정보 확인
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team

    # 자동생성된 document_id 중복 확인
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, schema.DocumentInfo):
        status_code, error = ErrorResponse.ErrorCode.get(2102)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_document_result, JSONResponse):
        status_code_no_document, _ = ErrorResponse.ErrorCode.get(2101)
        if select_document_result.status_code != status_code_no_document:
            return select_document_result
    
    # 업로드된 파일 포맷(확장자) 확인
    is_support = is_support_format(document_name)
    if is_support is False:
        status_code, error = ErrorResponse.ErrorCode.get(2105)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서 저장(minio or local pc)
    save_success, save_path = save_upload_document(document_id, document_name, document_data)
    if save_success:
        logger.info(f"success save document document_id : {document_id}")
        document_pages = get_page_count(document_data, document_name)
        dao_document_params = {
            "document_id": document_id,
            "user_email": user_email,
            "user_team": user_team,
            "document_path": save_path,
            "document_description": document_description,
            "document_pages": document_pages,
            "document_type": document_type
        }
        insert_document_result = query.insert_document(session, **dao_document_params)
        if isinstance(insert_document_result, JSONResponse):
            return insert_document_result
        
    else:
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
    ))
    
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
    )
    response.get("resource_id").update(document_id=document_id)
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response), background=background_tasks)
