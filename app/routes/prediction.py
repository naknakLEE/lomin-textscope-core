from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from typing import List, Dict

from app.database.connection import db
from app.common.const import get_settings
from app import models
from sqlalchemy.orm import Session
from app.utils.utils import cal_time_elapsed_seconds
from app.database import query
from app.utils.utils import load_image2base64, basic_time_formatter
from app.service.prediction import (
    get_all_prediction as get_all_prediction_service,
    get_cls_kv_prediction as get_cls_kv_prediction_service,
    get_gocr_prediction as get_gocr_prediction_service
)

settings = get_settings()
router = APIRouter()


@router.get("/")
def get_all_prediction(
    session: Session = Depends(db.session)
) -> JSONResponse:
    return get_all_prediction_service(session = session)
    


@router.get("/cls-kv")
def get_cls_kv_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    return get_cls_kv_prediction_service(
        task_id = task_id,
        visualize = visualize,
        session = session
    )


@router.get("/gocr")
def get_gocr_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    return get_gocr_prediction_service(
        task_id = task_id,
        visualize = visualize,
        session = session
    )