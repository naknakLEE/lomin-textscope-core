import requests  # type: ignore
import base64
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
from app.utils.minio import MinioService
from app.schemas import error_models as ErrorResponse


settings = get_settings()
router = APIRouter()
minio_client = MinioService()


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
def get_image(image_id: str, session: Session = Depends(db.session)) -> JSONResponse:
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
    
    image = select_image_result
    
    image_filename = Path(image.image_path)
    image_bytes = None
    if settings.USE_MINIO:
        image_minio_path = "/".join([image_id, image_filename.name])
        image_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET,)
    else:
        with Path(image.image_path).open("rb") as f:
            image_bytes = f.read()
    
    image = models.Image(
        filename=image_filename.name,
        width=0,
        height=0,
        upload_datetime=image.created_at,
        format=image_filename.suffix,
        data=base64.b64encode(image_bytes)
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


def save_upload_image(image_id: str, image_name: str, image_data):
    decoded_image_data = base64.b64decode(image_data)
    success = False
    save_path = ""
    if settings.USE_MINIO:
        success = minio_client.put(
            bucket_name=settings.MINIO_IMAGE_BUCKET,
            object_name=image_id + '/' + image_name,
            data=decoded_image_data,
        )
        save_path = "minio/" + image_name
    else:
        root_path = Path(settings.IMG_PATH)
        base_path = root_path.joinpath(image_id)
        base_path.mkdir(parents=True, exist_ok=True)
        save_path = base_path.joinpath(image_name)
        
        with save_path.open("wb") as file:
            file.write(decoded_image_data)
            
        success = True
    
    return success, save_path