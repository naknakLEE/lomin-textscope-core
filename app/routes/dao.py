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
from app.service.dao import (
    select_document as select_document_service,
    insert_inference_result as insert_inference_result_service
)

settings = get_settings()
router = APIRouter()


@router.get("/select/docx")
def select_document(
    document_id: str, 
    db: Session = Depends(db.session)
) -> Union[Optional[DocumentInfo], JSONResponse]:
    
    return select_document_service(
        document_id = document_id,
        db = db
    )


@router.post("/insert/inference")
def insert_inference_result(
    data: Dict = Body(...), \
    db: Session = Depends(db.session)
) -> bool:
    return insert_inference_result_service(
        data = data,
        db = db
    )
