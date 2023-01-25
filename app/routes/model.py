from typing import Any
from fastapi import APIRouter,  Depends
from sqlalchemy.orm import Session

from app.database.connection import db
from app.service.model import get_model as get_model_service

router = APIRouter()


@router.get("")
async def get_model(
    session: Session = Depends(db.session),
) -> Any:
    
    return await get_model_service(session = session)