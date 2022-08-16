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
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)
import base64

from app import hydra_cfg
from app.utils.background import bg_ocr_wrapper
from app.database.connection import db
from app.database import query, schema
from app.models import UserInfo as UserInfoInModel
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from app.utils.drm import document_path_verify
from app.utils.utils import cal_time_elapsed_seconds, get_ts_uuid
from app.utils.utils import is_admin, get_company_group_prefix
from app.schemas import error_models as ErrorResponse
from app.schemas import HTTPBearerFake
from app.middlewares.exception_handler import CoreCustomException
from app.utils.drm import load_file2base64, DRM
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
security = HTTPBearer() if hydra_cfg.route.use_token else HTTPBearerFake()


@router.get("/status", response_model=models.StatusResponse)
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


@router.get("/docx")
def get_image(
    document_id: str,
    page: int = 1,
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )
    
    document_path = Path(str(page) + ".png")
    document_bytes = get_image_bytes(document_id, document_path)
    
    document_base64, document_width, document_height, document_format = get_image_info_from_bytes(
            document_bytes,
            document_path.name,
            page
    )
    
    if document_bytes is None:
        raise CoreCustomException(2103)
    
    document = models.Image(
        filename=Path(select_document_result.document_path).name,
        description=select_document_result.document_description,
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
    
    user_email:           str = current_user.email
    document_id:          str = params.get("document_id", get_ts_uuid("document"))
    document_name:        str = params.get("file_name")
    document_data:        str = params.get("file")
    cls_type_idx:         int = params.get("cls_type_idx")
    doc_type_idx:         int = params.get("doc_type_idx")
    document_description: str = params.get("description")
    document_type:        str = params.get("document_type")
    document_path:        str = params.get("document_path")
    logger.info("start post /docx")
    # document_data가 없고 document_path로 요청이 왔는지 확인
    # document_path로 왔으면 파일 읽기
    if document_data is None and document_path is not None:
        document_data = load_file2base64(document_path)
    
    if hydra_cfg.common.drm.use: # drm 복호화
        drm = DRM()
        # TODO drm_user 수정 필요
        drm_user = "user01"
        document_data = await drm.drm_decryption(document_data, document_name, drm_user)
    logger.info("load document data")
    # 유저 정보 확인
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team
    logger.info("check user info")
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    logger.info("check user policy")
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    # 조회 가능 문서 종류(대분류) 확인
    # 조회 가능 문서 종류(소분류) 확인
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_list = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_list, JSONResponse):
        return cls_type_list
    
    docx_type_list: List[dict] = query.get_user_document_type(session, user_policy_result)
    if isinstance(docx_type_list, JSONResponse):
        return docx_type_list
    
    cls_type_idx_list: List[int] = list()
    doc_type_idx_list: List[int] = list()
    for cls_type in cls_type_list:
        cls_type_idx_list.append(cls_type.get("index"))
        doc_type_idx_list.extend( [ x.get("index") for x in cls_type.get("docx_type", [dict()]) ] )
        
    for docx_type in docx_type_list:
        doc_type_idx_list.append(docx_type.get("index"))
    
    # 요청한 문서 종류(대분류)가 요청 가능한 문서 종류 목록에 없을 경우 에러 반환
    # if cls_type_idx is not None and cls_type_idx not in list(set(cls_type_idx_list)):
    #     raise CoreCustomException(2509)
    
    # 요청한 문서 종류(소분류)가 요청 가능한 문서 종류 목록에 없을 경우 에러 반환
    # if doc_type_idx is not None and doc_type_idx not in list(set(doc_type_idx_list)):
    #     raise CoreCustomException(2509)
    
    # 자동생성된 document_id 중복 확인
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, schema.DocumentInfo):
        raise CoreCustomException(2102)
    elif isinstance(select_document_result, JSONResponse):
        status_code_no_document, _ = ErrorResponse.ErrorCode.get(2101)
        if select_document_result.status_code != status_code_no_document:
            return select_document_result
    
    # 업로드된 파일 포맷(확장자) 확인
    if is_support_format(document_name) is False:
        raise CoreCustomException(2105)
    
    logger.info(f"start save document name : {document_name}")
    # 문서 저장(minio or local pc)
    save_success, save_path = save_upload_document(document_id, document_name, document_data, separate=True)
    logger.info(f"start save document done name : {document_name}")
    
    if save_success is False:
        raise CoreCustomException(4102, "문서")
    
    logger.info(f"success save document document_id : {document_id}")
    document_pages = get_page_count(document_data, document_name)
    dao_document_params = {
        "document_id": document_id,
        "user_email": user_email,
        "user_team": user_team,
        "document_path": save_path,
        "document_description": document_description,
        "document_pages": document_pages,
        "cls_type_idx": cls_type_idx,
        "doc_type_idx": doc_type_idx,
        "document_type": document_type
    }
    insert_document_result = query.insert_document(session, **dao_document_params)
    if isinstance(insert_document_result, JSONResponse):
        return insert_document_result
    
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
    
    
    if hydra_cfg.document.background_ocr:
        # task_id = get_ts_uuid("task")
        # response.get("resource_id").update(task_id=task_id)
        
        # cls_type_idx(cls_idx)로 model_info 조회
        cls_model_info = None
        select_cls_group_model_result = query.select_cls_group_model(session, cls_idx=cls_type_idx)
        if isinstance(select_cls_group_model_result, JSONResponse):
            status_code_no_info, _ = ErrorResponse.ErrorCode.get(2108)
            if select_cls_group_model_result.status_code != status_code_no_info:
                return select_cls_group_model_result
            cls_model_info = None
        elif isinstance(select_cls_group_model_result, schema.ClsGroupModel):
            select_cls_group_model_result: schema.ClsGroupModel = select_cls_group_model_result
            cls_model_info: schema.ModelInfo = select_cls_group_model_result.model_info
        
        # doc_type_idx로 doc_type_code 조회
        doc_type_info = None
        select_doc_type_result = query.select_doc_type(session, doc_type_idx=doc_type_idx)
        if isinstance(select_doc_type_result, JSONResponse):
            status_code_no_info, _ = ErrorResponse.ErrorCode.get(2107)
            if select_doc_type_result.status_code != status_code_no_info:
                return select_doc_type_result
            doc_type_info = None
        elif isinstance(select_doc_type_result, schema.DocTypeInfo):
            doc_type_info: schema.DocTypeInfo = select_doc_type_result
        
        background_tasks.add_task(
            bg_ocr_wrapper,
            request,
            current_user,
            save_path=save_path,
            document_id=document_id,
            document_pages=document_pages,
            cls_model_info=cls_model_info,
            doc_type_info=doc_type_info
        )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response), background=background_tasks)


@router.post("/image/crop")
def image_crop(
    params: models.ParamPostImageCrop,
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    image_id = params.image_id
    
    select_image_result = query.select_image(session, image_id=image_id)
    if isinstance(select_image_result, JSONResponse):
        return select_image_result
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )
    
    data = dict(
        image_id=image_id,
        image_path=select_image_result.image_path,
        image_bytes=None,
        angle=params.rectification.rotated,
        page=params.page,
    )
    
    image = load_image(data)
    if image is None:
        raise CoreCustomException(2103)
    
    crop_images = get_crop_image(image, params.format, params.crop)
    if len(crop_images) == 0:
        raise CoreCustomException(2104)
    
    response.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
        format=params.format,
        crop=crop_images,
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))