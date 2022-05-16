import requests  # type: ignore
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from app.utils.utils import cal_time_elapsed_seconds
from app.schemas import error_models as ErrorResponse
from app.utils.image import (
    get_crop_image,
    get_image_info_from_bytes,
    get_image_bytes,
    save_upload_image,
    load_image,
)


settings = get_settings()
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


@router.get("/image")
def get_image(
    image_id: str,
    page: int = 1,
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
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
    
    image_path = Path(select_image_result.image_path)
    image_bytes = get_image_bytes(image_id, image_path)
    
    image_base64, image_width, image_height, image_format = get_image_info_from_bytes(
            image_bytes,
            image_path.name,
            page
    )
    
    if image_base64 is None:
        status_code, error = ErrorResponse.ErrorCode.get(2103)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    image = models.Image(
        filename=image_path.name,
        description=select_image_result.image_description,
        image_type=select_image_result.image_type,
        upload_datetime=select_image_result.created_at,
        width=image_width,
        height=image_height,
        format=image_format,
        data=image_base64
    )
    
    response.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            response_log=response_log,
            image_info=image,
        )
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.post("/image")
def upload_image(
    request: dict = Body(...), session: Session = Depends(db.session)
) -> JSONResponse:
    inputs = request
    response: Dict = dict()
    response_log: Dict = dict()
    request_datetime = datetime.now()
    image_id = inputs.get("image_id", "")
    image_name = inputs.get("file_name", "")
    image_data = inputs.get("file", "")
    
    select_image_result = query.select_image(session, image_id=image_id)
    
    if isinstance(select_image_result, schema.Image):
        status_code, error = ErrorResponse.ErrorCode.get(2102)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_image_result, JSONResponse):
        status_code_no_image, _ = ErrorResponse.ErrorCode.get(2101)
        if select_image_result.status_code != status_code_no_image:
            return select_image_result
    
    save_success, save_path = save_upload_image(image_id, image_name, image_data)
    if save_success:
        dao_image_params = {
            "image_id": image_id,
            "image_path": str(save_path),
            "image_type": inputs.get("image_type", "inference"),
            "image_description": inputs.get("description", ""),
        }
        insert_image_result = query.insert_image(session, **dao_image_params)
        if isinstance(insert_image_result, JSONResponse):
            return insert_image_result
    else:
        status_code, error = ErrorResponse.ErrorCode.get(4102)
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
    
    response.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            response_log=response_log,
        )
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


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
        status_code, error = ErrorResponse.ErrorCode.get(2103)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
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