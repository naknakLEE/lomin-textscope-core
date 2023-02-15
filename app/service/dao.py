import typing as t
from fastapi import APIRouter, Depends, Body
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from app import models
from app.utils.logging import logger
from app.database.schema import DocumentInfo
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse



def select_document(
    document_id: str, 
    db: Session
) -> t.Union[t.Optional[DocumentInfo], JSONResponse]:
    return query.select_document(db, document_id=document_id)


def insert_inference_result(
    data: t.Dict, 
    db: Session
)-> bool:
    return query.insert_inference_result(db, **data)