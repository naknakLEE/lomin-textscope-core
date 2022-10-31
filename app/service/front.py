from pathlib import Path
from loguru import logger
from requests import Session
from starlette.responses import JSONResponse
from app.schemas import error_models as ErrorResponse

from app.database.query import select_api_log_all, select_inference_all, select_inference_info
from fastapi.encoders import jsonable_encoder

from app.utils.image import get_image_bytes, image_to_base64, read_image_from_bytes

def get_task_list(
    session: Session, 
    **kwargs
) -> JSONResponse:
    """
        업무 목록을 불러옵니다.
    """
    try:
        total_count, result_list = select_inference_all(session, **kwargs)
        response = dict(
            total_count=total_count,
            task_list=result_list
        )
        return JSONResponse(status_code=200, content=jsonable_encoder(response))        
    except Exception:
        logger.exception("select_inference_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("업무목록 조회")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

def get_task_info(
    session: Session,
    inference_id: str
) -> JSONResponse:
    """
        업무 상세정보를 불러옵니다.
    """
    try:
        document_info, inference_info, inference_id_dict = select_inference_info(session, inference_id)

        # Inference result의 angle값을 구해서 해당 angle값 만큼 원본이미지 돌려서 return
        inference_result = inference_info.get('inference_result')
        angle = inference_result.get('angle', 0)
        document_path = document_info.get('document_path')
        origin_document_name = document_path.split('/')[1]
        document_extension = Path(document_path).suffix
        if document_extension.lower() in ['.pdf', '.tif', '.tiff']:
            document_path = document_path.replace(document_extension, '.png')

        document_bytes = get_image_bytes(document_info.get('document_id'), Path(document_path))
        
        accept_angle_image = read_image_from_bytes(document_bytes, document_path.split('/')[1], angle, 1)

        document_info.update(
            document_name = origin_document_name,
            document_data = image_to_base64(accept_angle_image)
        )
        del document_info['document_path']

        response = dict(
            document_info=document_info,
            inference_info=inference_info,
            inference_id=inference_id_dict
        )
        return JSONResponse(status_code=200, content=jsonable_encoder(response))        
    except Exception:
        logger.exception("select_inference_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("업무상세 조회")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))                       

def get_dashbaord_info(
    session: Session, 
    **kwargs
) -> JSONResponse:
    """
        대시보드 정보를 불러옵니다.
    """
    try:
        total_processing_dict, total_speed_dict = select_api_log_all(session, **kwargs)
        result = dict(
            processing_status = total_processing_dict,
            response_speed = total_speed_dict
        )
        return JSONResponse(status_code=200, content=jsonable_encoder(result))        
    except Exception:
        logger.exception("select_inference_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("대시보드 정보")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))           