from typing import Any
from fastapi import APIRouter,  Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from datetime import datetime
from app.utils.logging import logger
from app.database import query
from app.database.connection import db
from app.utils.router import init, response_metadata, model2response_data


async def get_model(
    session: Session,
) -> Any:
    # TODO 권한 추가 필요
    
    response, response_log, request_datetime = init()
    
    select_models_all_result = query.select_model_all(session)
    
    if isinstance(select_models_all_result, JSONResponse):
        return select_models_all_result
    
    response_model = model2response_data(select_models_all_result)
    
    response_datetime, elapsed = response_metadata(request_datetime)
    
    response.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        model=response_model
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))