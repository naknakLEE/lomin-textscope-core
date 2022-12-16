from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import UserInfo as UserInfoInModel
from fastapi import APIRouter, Body, Depends, Request
from fastapi.encoders import jsonable_encoder
from app.common.const import get_settings
from app.utils.background_task import QueueBackGroundTask

from app.utils.document import (
    document_file_verify,
    multiple_request_ocr,
    get_inference_result_to_pdf,
)
from app.utils.utils import cal_time_elapsed_seconds
from app.database.connection import db 
from app.utils.auth import get_current_active_user_fake as get_current_active_user

"""
    ### Nank2210 전용 API
"""

settings = get_settings()   # default setting
router = APIRouter()
queue_background_task = QueueBackGroundTask()


@router.post("/inference/ocr")
async def post_inference_ocr(
    request: Request,
    inputs: Dict = Body(...),
    # background_tasks: BackgroundTasks = BackgroundTasks(),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [CAMS-OCR] Searchable_pdf 생성
    document_dir로 입력받은 Nas경로 폴더 안에 있는 모든 파일을 ocr 후 pdf_file_name으로 입력받은 경로에 searchable_pdf를 생성합니다.
    pdf 생성이 성공하면 document_dir 폴더를 삭제합니다. 
    """

    response: dict = dict()
    response_log: dict = dict()

    # 시작 시간 측정
    request_datetime = datetime.now()

    log_api_uuid = request.state.api_id
    inputs.update(
        log_api_uuid=log_api_uuid
    )
    queue_background_task.add_task(
        multiple_request_ocr,
        inputs,
        session
    )

    # 종료 시간 측정 
    response_datetime = datetime.now()
    # 걸린 시간 측정 (종료시간 - 시작시간)
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)

    

    # response log 생성(시작시간, 종료시간, 걸린시간)
    response_log.update(
        dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        )
    )
    
    

    # response 객체 생성
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        log_api_uuid=log_api_uuid
    )    

    return JSONResponse(status_code=200, content=jsonable_encoder(response))



@router.put("/pdf")
async def put_pdf(
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    # background_tasks: BackgroundTasks = BackgroundTasks(),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [CAMS-OCR] Searchable_pdf 수정 요청
    pdf_dir 입력받은 Nas경로 폴더 안에 있는 pdf 파일을 가져와 textscope front화면으로 등록 합니다.
    등록 완료시 put_dir 입력받은 폴더를 삭제합니다.
    """
    response: dict = dict()
    response_log: dict = dict()

    # 시작 시간 측정
    request_datetime = datetime.now()

    pdf_dir      :str = inputs.get("pdf_dir")

    path_verify = document_file_verify(pdf_dir)
    if isinstance(path_verify, JSONResponse): return path_verify
    log_api_uuid = request.state.api_id
    inputs.update(
        user_email=current_user.email,
        user_team=current_user.team,   
        log_api_uuid=log_api_uuid
    )

    queue_background_task.add_task(
        get_inference_result_to_pdf,
        inputs,
        session
    )    

    # 종료 시간 측정 
    response_datetime = datetime.now()
    # 걸린 시간 측정 (종료시간 - 시작시간)
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)

    

    # response log 생성(시작시간, 종료시간, 걸린시간)
    response_log.update(
        dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        )
    )
    
    # response 객체 생성
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
    )    

    return JSONResponse(status_code=200, content=jsonable_encoder(response))