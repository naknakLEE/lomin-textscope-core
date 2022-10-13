from typing import Dict, Union, Optional, List
from fastapi import APIRouter, Depends, Body
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from app import models
from app.utils.logging import logger
from app.database.schema import DocumentInfo
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

settings = get_settings()
router = APIRouter()


@router.get("/select/docx")
def select_document(document_id: str, db: Session = Depends(db.session)) -> Union[Optional[DocumentInfo], JSONResponse]:
    return query.select_document(db, document_id=document_id)


@router.post("/insert/inference")
def insert_inference_result(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> bool:
    # logger.info(data)
    return query.insert_inference_result(db, **data)
