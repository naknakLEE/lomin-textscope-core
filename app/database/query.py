import json
import uuid
from fastapi import HTTPException
from typing import Any, Dict, List, Union, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app import models
from app.database import schema
from app.utils.logging import logger
from app.database.connection import Base
from app.schemas import error_models as ErrorResponse


def select_document(session: Session, **kwargs: Dict) -> Union[schema.DocumentInfo, JSONResponse]:
    dao = schema.DocumentInfo
    try:
        result = dao.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def insert_document(
    session: Session,
    employee_num: int,
    user_personnel: str,
    document_path: str,
    document_id: str = str(uuid.uuid4()),
    document_description: Optional[str] = None,
    document_type: str = "TRAINING",
    document_pages: int = 0,
    auto_commit: bool = True
) -> Union[Optional[schema.DocumentInfo], JSONResponse]:
    dao = schema.DocumentInfo
    try:
        result = dao.create(
            session=session,
            document_id=document_id,
            employee_num=employee_num,
            user_personnel=user_personnel,
            document_path=document_path,
            document_description=document_description,
            document_type=document_type,
            document_pages=document_pages,
            auto_commit=auto_commit
        )
    except Exception as e:
        logger.error(f"document insert error: {e}")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def insert_inference(
    session: Session,
    inference_id: str,
    document_id: str,
    employee_num: int,
    user_personnel: str,
    model_index: int,
    inference_result: dict,
    page_id: str,
    inference_type: str,
    response_log: dict,
    auto_commit: bool = True
) -> Union[None, JSONResponse]:
    
    del inference_result["response_log"]
    try:
        result = schema.InferenceInfo.create(
            session=session,
            inference_id=inference_id,
            document_id=document_id,
            employee_num=employee_num,
            user_personnel=user_personnel,
            model_index=model_index,
            inference_result=jsonable_encoder(inference_result),
            page_id=page_id,
            inference_type=inference_type,
            inference_start_time=response_log.get("inference_start_time"),
            inference_end_time=response_log.get("inference_end_time"),
            auto_commit=auto_commit
        )
    except Exception:
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4701)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_page_info(
    session: Session,
    page_id: str,
    page_num: int = 1,
    page_doc_type: str = "sample_doc_type",
    page_width: int = 0,
    page_height: int = 0,
    auto_commit: bool = True
) -> Union[None, JSONResponse]:
    
    dao = schema.PageInfo
    try:
        result = dao.create(
            session=session,
            page_id=page_id,
            page_num=page_num,
            page_doc_type=page_doc_type,
            page_width=page_width,
            page_height=page_height,
            auto_commit=auto_commit
        )
    except Exception:
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4601)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_task(session: Session, **kwargs: Dict) -> Union[schema.TaskInfo, JSONResponse]:
    dao = schema.TaskInfo
    try:
        result = dao.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2201)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("task select error")
        status_code, error = ErrorResponse.ErrorCode.get(4201)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_task(
    session: Session,
    task_id: str,
    employee_num: int,
    user_personnel: str,
    task_content: dict = {},
    auto_commit: bool = True
) -> Union[Optional[schema.TaskInfo], JSONResponse]:
    
    dao = schema.TaskInfo
    try:
        result = dao.create(
            session=session,
            task_id=task_id,
            employee_num=employee_num,
            user_personnel=user_personnel,
            task_content=jsonable_encoder(task_content),
            auto_commit=auto_commit
        )
    except Exception:
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4202)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_user(session: Session, **kwargs: Dict) -> schema.UserInfo:
    dao = schema.UserInfo
    try:
        result = dao.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user select error")
        status_code, error = ErrorResponse.ErrorCode.get(4502)
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result
