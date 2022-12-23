from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.database.connection import db
from app.common.const import get_settings
from app import models
from app.service.categories import get_model_categories as get_model_categories_service
from sqlalchemy.orm import Session


settings = get_settings()
router = APIRouter()


@router.get("/categories")
def get_model_categories(
    model_id: str, session: Session = Depends(db.session)
) -> JSONResponse:
    return get_model_categories_service(
        model_id = model_id,
        session = session
    )
