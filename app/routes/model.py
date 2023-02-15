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
from app.service.model import get_model as get_model_service

router = APIRouter()


@router.get("")
async def get_model(
    session: Session = Depends(db.session),
) -> Any:
    
    return await get_model_service(session = session)