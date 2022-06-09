import json
import uuid

from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
from typing import Any, Dict, List, Union, Optional, Tuple
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
        error.error_message = "문서 " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_document_all(session: Session, **kwargs: Dict) -> Union[schema.DocumentInfo, JSONResponse]:
    dao = schema.DocumentInfo
    try:
        result = dao.get_all(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "문서 " + error.error_message
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
    except Exception:
        logger.error(f"document insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = "문서 " + error.error_message
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
) -> Union[Optional[schema.InferenceInfo], JSONResponse]:
    
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
        logger.error(f"inference insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = "추론 " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_inspect_all(session: Session, start_date: datetime, end_date: datetime, **kwargs: Dict) -> Union[schema.InspectInfo, JSONResponse]:
    dao = schema.InspectInfo
    try:
        result = dao.get_all(session, start_date, end_date, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "검수 " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_document_inspect_all(
    session: Session,
    start_date: datetime,
    end_date: datetime,
    
    user_personnel: List[str],
    uploader_list: List[str],
    inspecter_list: List[str],
    document_type: List[str],
    document_model_type: List[str],
    inspect_status: List[str]
) -> list:
    
    query = session.query(schema.DocumentInfo, schema.InspectInfo) \
        .filter(schema.DocumentInfo.inspect_id == schema.InspectInfo.inspect_id)
    
    rows: List[Tuple[schema.DocumentInfo, schema.InspectInfo]] = query.all()
    
    filtered_rows = list()
    for row in rows:
        document_info, inspect_info = row
        
        if len(user_personnel) > 0 and document_info.user_personnel not in user_personnel: continue
        if len(document_type) > 0 and document_info.document_type not in document_type: continue
        if len(document_model_type) > 0 and document_info.document_model_type not in document_model_type: continue
        if len(uploader_list) > 0 and document_info.employee_num not in uploader_list: continue
        
        if len(inspecter_list) > 0 and inspect_info.employee_num not in inspecter_list: continue
        if len(inspect_status) > 0 and inspect_info.inspect_status not in inspect_status: continue
        if inspect_info.inspect_end_time < start_date or \
            end_date < inspect_info.inspect_end_time: continue
        
        filtered_rows.append([
            document_info.document_id,
            document_info.user_personnel,
            document_info.document_type,
            document_info.document_model_type,
            Path(document_info.document_path).name,
            document_info.employee_num,
            document_info.document_upload_time,
            
            inspect_info.employee_num,
            inspect_info.inspect_status,
            inspect_info.inspect_accuracy,
            inspect_info.inspect_end_time
        ])
    
    return filtered_rows


def insert_page_info(
    session: Session,
    page_id: str,
    page_num: int = 1,
    page_doc_type: str = None,
    page_width: int = 0,
    page_height: int = 0,
    auto_commit: bool = True
) -> Union[Optional[schema.PageInfo], JSONResponse]:
    
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
        logger.error(f"page_info insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = "page " + error.error_message
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
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "사용자의 그룹(권한, 역할) " + error.error_message
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
        logger.error(f"task insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = "task " + error.error_message
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
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "사용자 " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_user_all(session: Session, **kwargs: Dict) -> Union[schema.UserInfo, JSONResponse]:
    dao = schema.UserInfo
    try:
        result = dao.get_all(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "사용자 " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_user_role(session: Session, **kwargs: Dict) -> schema.UserRole:
    dao = schema.UserRole
    try:
        result = dao.get_lastest_role(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user_role select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "사용자의 그룹(권한, 역할) " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_role_info(session: Session, **kwargs: Dict) -> schema.RoleInfo:
    dao = schema.RoleInfo
    try:
        result = dao.get_lastest_role(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("role_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = "그룹(권한, 역할) " + error.error_message
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result