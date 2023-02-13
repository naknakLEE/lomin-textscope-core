import os
import requests  # type: ignore

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
from httpx import Client
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi import BackgroundTasks
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

import base64

from app.services.index import request_rotator
from app.utils.background import bg_ocr
from app.database.connection import db
from app.database import query, schema
from app.models import UserInfo as UserInfoInModel
from app.wrapper import pipeline
from app.common.const import settings
from app.utils.logging import logger
from app import models
from app.wrapper.pipeline import rotate_
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
    read_image_from_bytes,
    load_image,
)
from app.service.index import (
    check_status as check_status_service,
    get_image as get_image_service,
    post_upload_document as post_upload_document_service,
    post_document_image_crop as post_document_image_crop_service
    
)
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


@router.get("/status", response_model=models.StatusResponse)
def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    -  is_pp_server_working: 후처리 서버와 연결 상태 확인
    """
    return check_status_service()

@router.get("/docx")
def get_image(
    document_id: str,
    page: int = 1,
    rotate: bool = False,
    session: Session = Depends(db.session)
) -> JSONResponse:
    return get_image_service(
        document_id = document_id, 
        page = page, 
        rotate = rotate, 
        session = session
    )

@router.post("/docx")
async def post_upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    params: dict = Body(...), 
    session: Session = Depends(db.session),
) -> JSONResponse:
    
    return await post_upload_document_service(
        request = request,
        background_tasks = background_tasks,
        current_user = current_user,
        params = params,
        session = session
    )


@router.post("/docx/image/crop")
def post_document_image_crop(
    params: models.ParamPostImageCrop,
    session: Session = Depends(db.session)
) -> JSONResponse:
    return post_document_image_crop_service(
        params = params,
        session = session
    )