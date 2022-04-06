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
from app.database import query
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from app.utils.utils import cal_time_elapsed_seconds
from app.utils.minio import MinioService


settings = get_settings()
router = APIRouter()
minio_client = MinioService()


class Error400(models.CommonErrorResponse):
    error = models.Error(error_code="400", error_message="already exist")


class Error404(models.CommonErrorResponse):
    error = models.Error(error_code="404", error_message="not found")


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
def get_image(image_path: str, session: Session = Depends(db.session)) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()

    result = query.select_image(session, image_path=image_path)
    if not result:
        raise HTTPException(status_code=404, detail=vars(Error404().error))
    image_id = result.image_id

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
            image_id=image_id,
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
    image_data = inputs.get("file", "")
    image_name = inputs.get("file_name", "")
    image_id = inputs.get("image_id", "")
    decoded_image_data = base64.b64decode(image_data)
    
    if query.select_image(session, image_id=image_id):
        logger.warning(f"{image_id} is already exists")
        return HTTPException(status_code=400, detail=f"{image_id} is already exists")
        
    upload_success = False
    save_path = ""
    if settings.USE_MINIO:
        upload_success = minio_client.put(
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
            
        upload_success = True
    
    if upload_success:
        dao_image_params = {
            "image_id": image_id,
            "image_path": str(save_path),
            "image_type": inputs.get("image_type", "inference"),
            "image_description": inputs.get("description", ""),
        }
        query.insert_image(session, **dao_image_params)
    else:
        return HTTPException(status_code=400, detail=f"{image_name} was not saved")
    
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
