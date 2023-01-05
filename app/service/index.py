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
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

import base64

from app.config import hydra_cfg
from app.services.index import request_rotator
from app.utils.background import bg_ocr
from app.database.connection import db
from app.database import query, schema
from app.models import UserInfo as UserInfoInModel
from app.wrapper import pipeline
from app.common.const import get_settings
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
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


settings = get_settings()


def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    -  is_pp_server_working: 후처리 서버와 연결 상태 확인
    """
    try:
        is_serving_server_working = "False"
        serving_server_addr = (
            f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
        )
        serving_server_status_check_url = f"{serving_server_addr}/livez"
        response = requests.get(serving_server_status_check_url)
        if response.status_code == 200:
            is_serving_server_working = "True"
    except:
        logger.exception("check serving server status")

    try:
        is_pp_server_working = "False"
        pp_server_addr = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"
        pp_server_status_check_url = f"{pp_server_addr}/status"
        response = requests.get(pp_server_status_check_url)
        if response.status_code == 200:
            is_pp_server_working = "True"
    except:
        logger.exception("check pp server status")

    try:
        session = next(db.session())
        session.execute("SELECT 1")
        is_database_working = "True"
    except:
        is_database_working = "False"
    finally:
        session.close()

    status = dict(
        is_database_working=is_database_working,
        is_serving_server_working=is_serving_server_working,
        is_pp_server_working=is_pp_server_working,
    )
    return JSONResponse(content=jsonable_encoder(status))


def get_image(
    document_id: str,
    page: int,
    rotate: bool,
    session: Session
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )
    
    document_path = Path(select_document_result.document_path)
    document_bytes = get_image_bytes(document_id, document_path)
    
    document_base64, document_width, document_height, document_format = get_image_info_from_bytes(
            document_bytes,
            document_path.name,
            page
    )
    
    if document_bytes is None:
        status_code, error = ErrorResponse.ErrorCode.get(2103)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    if rotate:
        document_base64 = request_rotator(session, document_id, document_bytes)
        if isinstance(document_base64, JSONResponse):
            return document_base64
    
    document = models.Image(
        filename=document_path.name,
        description=select_document_result.document_description,
        image_type="inference",
        upload_datetime=select_document_result.document_upload_time,
        width=document_width,
        height=document_height,
        format=document_format,
        data=document_base64
    )
    
    
    response.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
        document_info=document,
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


async def post_upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserInfoInModel,
    params: dict, 
    session: Session,
) -> JSONResponse:
    
    response: dict = dict(resource_id=dict())
    response_log: dict = dict()
    request_datetime = datetime.now()
    
    user_email:            str = current_user.email
    document_id:          str = params.get("document_id", get_ts_uuid("document"))
    document_name:        str = params.get("file_name")
    document_data:        str = params.get("file")
    cls_type_idx:         int = params.get("cls_type_idx")
    doc_type_idx:         int = params.get("doc_type_idx")
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
    
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 조회 가능 문서 종류(대분류) 확인
    # 조회 가능 문서 종류(소분류) 확인
    cls_type_list: List[dict] = query.get_user_classification_type(session, user_policy_result)
    docx_type_list: List[dict] = query.get_user_document_type(session, user_policy_result)
    
    cls_type_idx_list: List[int] = list()
    doc_type_idx_list: List[int] = list()
    for cls_type in cls_type_list:
        cls_type_idx_list.append(cls_type.get("index"))
        doc_type_idx_list.extend( [ x.get("index") for x in cls_type.get("docx_type", [dict()]) ] )
        
    for docx_type in docx_type_list:
        doc_type_idx_list.append(docx_type.get("index"))
    
    # 요청한 문서 종류(대분류)가 조회 가능한 문서 목록에 없을 경우 에러 반환
    if cls_type_idx is not None and cls_type_idx not in list(set(cls_type_idx_list)):
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 요청한 문서 종류(소분류)가 조회 가능한 문서 목록에 없을 경우 에러 반환
    if doc_type_idx is not None and doc_type_idx not in list(set(doc_type_idx_list)):
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
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
    
    document_pages, document_name = get_page_count(document_data, document_name)
    
    # 문서 저장(minio or local pc)
    save_success, save_path = save_upload_document(document_id, document_name, document_data)
    if save_success:
        # doc_type_index로 doc_type_code 조회
        select_doc_type_result = query.select_doc_type(session, doc_type_idx=doc_type_idx)
        if isinstance(select_doc_type_result, JSONResponse):
            return select_doc_type_result
        select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
        doc_type_code = select_doc_type_result.doc_type_code
        
        logger.info(f"success save document document_id : {document_id}")
        dao_document_params = {
            "document_id": document_id,
            "user_email": user_email,
            "user_team": user_team,
            "document_path": save_path,
            "document_description": document_description,
            "document_pages": document_pages,
            "doc_type_idx": doc_type_idx,
            "document_type": document_type
        }
        insert_document_result = query.insert_document(session, **dao_document_params)
        if isinstance(insert_document_result, JSONResponse):
            return insert_document_result
        
        if hydra_cfg.document.background_ocr:
            # task_id = get_ts_uuid("task")
            # response.get("resource_id").update(task_id=task_id)
            background_tasks.add_task(
                bg_ocr,
                request,
                current_user,
                save_path=save_path,
                document_id=document_id,
                document_pages=document_pages,
                doc_type_code=doc_type_code
            )
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



def post_document_image_crop(
    params: models.ParamPostImageCrop,
    session: Session
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    document_id = params.document_id
    page_num = params.page
    angle = params.rectification.rotated
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서의 page_num 페이지의 썸네일 base64로 encoding
    document_path = Path(select_document_result.document_path)
    document_bytes = get_image_bytes(document_id, document_path)
    image = read_image_from_bytes(document_bytes, document_path.name, (-1 * angle), page_num)
    if image is None:
        status_code, error = ErrorResponse.ErrorCode.get(2103)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )
    
    crop_images = get_crop_image(image, params.format, params.crop)
    if len(crop_images) == 0:
        status_code, error = ErrorResponse.ErrorCode.get(2104)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    response.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
        format=params.format,
        crop=crop_images,
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))