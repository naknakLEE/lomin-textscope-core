from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import UserInfo as UserInfoInModel
from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from app import hydra_cfg
from app.common.const import get_settings
from fastapi import BackgroundTasks

from app.utils.document import (
    document_dir_verify,
    multiple_request_ocr,
    generate_searchalbe_pdf,
    save_minio_pdf_convert_img,
    get_inference_result_to_pdf
)
from app.utils.minio import MinioService
from app.utils.utils import cal_time_elapsed_seconds
from app.database.connection import db 
from app.utils.auth import get_current_active_user_fake as get_current_active_user
# if hydra_cfg.route.use_token:
#     from app.utils.auth import get_current_active_user as get_current_active_user
# else:
#     from app.utils.auth import get_current_active_user_fake as get_current_active_user

"""
    ### Nank2210 전용 API
"""

settings = get_settings()   # default setting
router = APIRouter()


@router.post("/inference/ocr")
async def post_inference_ocr(
    inputs: Dict = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

    document_dir      :str = inputs.get("document_dir")

    path_verify = document_dir_verify(document_dir)
    if isinstance(path_verify, JSONResponse): return path_verify

    background_tasks.add_task(
        multiple_request_ocr,
        inputs        
    )
    
    # inference_result_list = multiple_request_ocr(inputs)
    # if(isinstance(inference_result_list, JSONResponse)): return inference_result_list
    # # document_cnt로 sort(순서 보장을 위해)
    # sorted(inference_result_list, key=lambda k: k['cnt'])

    # inputs.update(
    #     inference_result_list=inference_result_list
    # )
    
    # pdf_result = generate_searchalbe_pdf(inputs)
    # if(isinstance(pdf_result, JSONResponse)): return pdf_result

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



@router.put("/pdf")
async def put_pdf(
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

    path_verify = document_dir_verify(pdf_dir)
    if isinstance(path_verify, JSONResponse): return path_verify

    inputs.update(
        user_email=current_user.email,
        user_team=current_user.team,   
    )

    background_tasks.add_task(
        get_inference_result_to_pdf,
        inputs,
        session        
    )    

    # current_user_info = dict(
    #     user_email=current_user.email,
    #     user_team=current_user.team
    # )
    # pdf_len, document_id, origin_object_name = save_minio_pdf_convert_img(inputs, session, current_user_info)
    # if(isinstance(pdf_len, JSONResponse)): return pdf_len

    # pdf_extract_inputs = dict(
    #     pdf_len = pdf_len,
    #     document_id = document_id,
    #     origin_object_name = origin_object_name,
    #     pdf_dir = pdf_dir
    # )
    # inference_result_list = get_inference_result_to_pdf(pdf_extract_inputs, session)
    # if(isinstance(inference_result_list, JSONResponse)): return inference_result_list


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