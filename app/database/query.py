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
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import Base
from app.schemas import error_models as ErrorResponse


settings = get_settings()

def select_model_all(session: Session, **kwargs: Dict) -> Union[schema.ModelInfo, JSONResponse]:
    dao = schema.ModelInfo
    try:
        result = dao.get_all(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2106)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4103)
        error.error_message = error.error_message.format("문서")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result
        
    

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
        error.error_message = error.error_message.format("문서")
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
        error.error_message = error.error_message.format("모든 문서")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def insert_document(
    session: Session,
    user_email: int,
    user_team: str,
    document_path: str,
    document_id: str = str(uuid.uuid4()),
    document_description: Optional[str] = None,
    document_model_type: int = None,
    document_type: str = "TRAINING",
    document_pages: int = 0,
    auto_commit: bool = True
) -> Union[Optional[schema.DocumentInfo], JSONResponse]:
    dao = schema.DocumentInfo
    try:
        result = dao.create(
            session=session,
            document_id=document_id,
            user_email=user_email,
            user_team=user_team,
            document_path=document_path,
            document_description=document_description,
            document_type=document_type,
            document_pages=document_pages,
            auto_commit=auto_commit,
            document_model_type=document_model_type
        )
    except Exception:
        logger.error(f"document insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_inference_latest(session: Session, **kwargs: Dict) -> schema.InferenceInfo:
    dao = schema.InferenceInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.inference_end_time.desc()).first()
        
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2507)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("inference select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("추론")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_inference(
    session: Session,
    inference_id: str,
    document_id: str,
    user_email: int,
    user_team: str,
    model_index: int,
    inference_result: dict,
    inference_type: str,
    page_num: int,
    response_log: dict,
    auto_commit: bool = True
) -> Union[Optional[schema.InferenceInfo], JSONResponse]:
    
    del inference_result["response_log"]
    try:
        result = schema.InferenceInfo.create(
            session=session,
            inference_id=inference_id,
            document_id=document_id,
            user_email=user_email,
            user_team=user_team,
            model_index=model_index,
            inference_result=jsonable_encoder(inference_result),
            inference_type=inference_type,
            inference_start_time=response_log.get("inference_start_time"),
            inference_end_time=response_log.get("inference_end_time"),
            
            page_num=page_num,
            page_doc_type=inference_result.get("doc_type", "None"),
            page_width=inference_result.get("image_width_origin", 0),
            page_height=inference_result.get("image_height_origin", 0),
            auto_commit=auto_commit
        )
    except Exception:
        logger.error(f"inference insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("추론")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_inspect_latest(session: Session, **kwargs: Dict) -> Union[schema.InspectInfo, JSONResponse]:
    dao = schema.InspectInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.inspect_end_time.desc()).first()
        
    except Exception:
        logger.exception("inspect select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("가장 최근 검수")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_inspect_all(session: Session, start_date: datetime, end_date: datetime, **kwargs: Dict) -> Union[schema.InspectInfo, JSONResponse]:
    dao = schema.InspectInfo
    try:
        query = dao.get_all(session, kwargs)
        query = query.filter(dao.inspect_end_time.between(start_date, end_date))
        result = query.all() if query else None
        
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("inspect select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 검수")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_document_inspect_all(
    session: Session,
    ignore_date: bool,
    start_date: datetime,
    end_date: datetime,
    
    user_team: List[str] = [],
    uploader_list: List[str] = [],
    inspecter_list: List[str] = [],
    document_type: List[str] = [],
    document_model_type: List[str] = [],
    inspect_status: List[str] = [],
    
    rows_limit: int = 100,
    rows_offset: int = 0,
    column_order: list = [],
) -> list:
    
    try:
        # table join (inspect_id)
        query = session.query(schema.DocumentInfo, schema.InspectInfo) \
            .filter(schema.DocumentInfo.inspect_id == schema.InspectInfo.inspect_id)
        
        # 총 업무 개수
        if len(user_team) > 0: query = query.filter(schema.DocumentInfo.user_team.in_(user_team))
        total_count = query.count()
        
        # DocumentInfo 필터링
        document_filters = dict(
            document_type=document_type,
            document_model_type=document_model_type,
            uploader_list=uploader_list
        )
        
        for column, filter in document_filters.items():
            if len(filter) > 0: query = query.filter(getattr(schema.DocumentInfo, column).in_(filter))
        
        # InsepctInfo 필터링
        inspect_filters = dict(
            inspecter_list=inspecter_list,
            inspect_status=inspect_status
        )    
        for column, filter in inspect_filters.items():
            if len(filter) > 0: query = query.filter(getattr(schema.InspectInfo, column).in_(filter))
        
        # 완료 업무 개수
        complet_count = query.filter(schema.InspectInfo.inspect_end_time != None).count()
        
        # InspectInfo 검수 완료일 필터링
        if ignore_date is False:
            query = query.filter(schema.InspectInfo.inspect_end_time != None)
            query = query.filter(schema.InspectInfo.inspect_end_time.between(start_date, end_date))
        
        # 페이징
        query = query.offset(rows_offset).limit(rows_limit)
        
        rows: List[Tuple[schema.DocumentInfo, schema.InspectInfo]] = query.all()
        filtered_rows = list()
        table_mapping = {"DocumentInfo": None, "InspectInfo": None}
        for row in rows:
            
            table_mapping.update(DocumentInfo=row[0])
            table_mapping.update(InspectInfo=row[1])
            
            row_ordered: list = list()
            for table_column in column_order:
                t, c = table_column.split(".")
                v = getattr(table_mapping.get(t), c)
                row_ordered.append(v)
            
            filtered_rows.append(row_ordered)
        
    except Exception:
        logger.exception("document_inspcet_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("필터링된 업무 리스트")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        return 0, 0, result
    
    return total_count, complet_count, filtered_rows


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
        error.error_message = error.error_message.format("task")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_task(
    session: Session,
    task_id: str,
    user_email: int,
    user_team: str,
    task_content: dict = {},
    auto_commit: bool = True
) -> Union[Optional[schema.TaskInfo], JSONResponse]:
    
    dao = schema.TaskInfo
    try:
        result = dao.create(
            session=session,
            task_id=task_id,
            user_email=user_email,
            user_team=user_team,
            task_content=jsonable_encoder(task_content),
            auto_commit=auto_commit
        )
    except Exception:
        logger.error(f"task insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("task")
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
        error.error_message = error.error_message.format("사용자")
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
        logger.exception("user_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 사용자")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_user_role_latest(session: Session, **kwargs: Dict) -> schema.UserRole:
    dao = schema.UserRole
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.created_time.desc()).first()
        
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user_role select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("사용자의 그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_role_info(session: Session, **kwargs: Dict) -> schema.RoleInfo:
    dao = schema.RoleInfo
    try:
        result = dao.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("role_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_org_all(session: Session, **kwargs: Dict) -> schema.KeiOrgInfo:
    dao = schema.KeiOrgInfo
    try:
        result = dao.get_all(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("kei_org_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("수출입은행 조직도")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result