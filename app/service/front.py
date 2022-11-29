from loguru import logger
from requests import Session
from starlette.responses import JSONResponse
from app.schemas import error_models as ErrorResponse

from app.database.query import select_api_log_all
from fastapi.encoders import jsonable_encoder

      

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