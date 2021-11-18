import requests
import base64
import zipfile
import os

from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Request, Body, Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from sqlalchemy.orm import Session
from app.utils.utils import cal_time_elapsed_seconds


settings = get_settings()
router = APIRouter()

@router.get("/categories")
def get_model_categories(
    model_id: str,
    session: Session = Depends(db.session) 
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    # @TODO: select db where model_id
    
    # test용 데이터
    categories = [
        models.Category(
            code="A01",
            name="주민등록증"
        ),
        models.Category(
            code="A02",
            name="운전면허증"
        )
    ]
    
    response.update(dict(
        categories=categories
    ))
    response_datetime = datetime.now()
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        response=response
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))