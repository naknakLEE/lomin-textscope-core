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


def select_doc_type(session: Session, **kwargs: Dict) -> Union[schema.DocTypeInfo, JSONResponse]:
    try:
        result = schema.DocTypeInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("doc_type select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("문서 종류")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result
    


def select_doc_type_all(session: Session, **kwargs: Dict) -> Union[List[schema.DocTypeInfo], JSONResponse]:
    try:
        result = schema.DocTypeInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("doc_type_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 문서 종류")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result
    


def select_model(session: Session, **kwargs: Dict) -> Union[schema.ModelInfo, JSONResponse]:
    try:
        result = schema.ModelInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2106)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모델")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result
    


def select_model_all(session: Session, **kwargs: Dict) -> Union[List[schema.ModelInfo], JSONResponse]:
    try:
        result = schema.ModelInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2106)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("model_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 모델")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_document(session: Session, **kwargs: Dict) -> Union[schema.DocumentInfo, JSONResponse]:
    try:
        result = schema.DocumentInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("document select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("문서")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def insert_document(
    session: Session,
    user_email: int,
    user_team: str,
    document_path: str,
    document_id: str = str(uuid.uuid4()),
    document_description: Optional[str] = None,
    document_type: str = "TRAINING",
    document_pages: int = 0,
    doc_type_idx: int = 0,
    auto_commit: bool = True
) -> Union[Optional[schema.DocumentInfo], JSONResponse]:
    try:
        result = schema.DocumentInfo.create(
            session=session,
            document_id=document_id,
            user_email=user_email,
            user_team=user_team,
            document_path=document_path,
            document_description=document_description,
            document_type=document_type,
            document_pages=document_pages,
            doc_type_idx=doc_type_idx,
            auto_commit=auto_commit,
        )
    except Exception:
        logger.error(f"document insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def update_document(session: Session, document_id: str, **kwargs: Dict) -> Union[Optional[schema.DocumentInfo], JSONResponse]:
    try:
        result = schema.DocumentInfo.update(
            session=session,
            p_key="document_id",
            p_value=document_id,
            **kwargs
        )
    except Exception:
        logger.error(f"document update error")
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
        error.error_message = error.error_message.format("최근 추론")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_inference(
    session: Session,
    inference_id: str,
    document_id: str,
    user_email: int,
    user_team: str,
    inference_result: dict,
    inference_type: str,
    page_num: int,
    doc_type_idx: int,
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
            inference_result=jsonable_encoder(inference_result),
            inference_type=inference_type,
            inference_start_time=response_log.get("inference_start_time"),
            inference_end_time=response_log.get("inference_end_time"),
            
            page_num=page_num,
            doc_type_idx=doc_type_idx,
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


def insert_inspect(session: Session, **kwargs: Dict) -> Union[Optional[schema.InspectInfo], JSONResponse]:
    try:
        result = schema.InspectInfo.create(session=session, **kwargs)
    except Exception:
        logger.error(f"inference insert error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("추론")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_document_inspect_all(
    session: Session,
    ignore_date: bool,
    start_date: datetime,
    end_date: datetime,
    
    user_team: List[str] = [],
    uploader_list: List[str] = [],
    inspecter_list: List[str] = [],
    # document_type: List[str] = [],
    doc_type_idx_list: List[int] = [],
    inspect_status: List[str] = [],
    
    rows_limit: int = 100,
    rows_offset: int = 0,
    column_order: list = [],
) -> Union[List[Tuple[int, int, list]], JSONResponse]:
    
    try:
        # table join (inspect_id)
        query = session.query(schema.DocumentInfo, schema.InspectInfo) \
            .filter(schema.DocumentInfo.inspect_id == schema.InspectInfo.inspect_id) \
            .order_by(schema.DocumentInfo.document_upload_time.desc())
        
        # 총 업무 개수
        if len(user_team) > 0: query = query.filter(schema.DocumentInfo.user_team.in_(user_team))
        total_count = query.count()
        
        # DocumentInfo 필터링
        document_filters = dict(
            # document_type=document_type,
        doc_type_idx=doc_type_idx_list,
            user_email=uploader_list
        )
        for column, filter in document_filters.items():
            if len(filter) > 0: query = query.filter(getattr(schema.DocumentInfo, column).in_(filter))
        
        # InsepctInfo 필터링
        inspect_filters = dict(
            user_email=inspecter_list,
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
        
        # 페이징 (한 요청당 최대 1000개)
        query = query.offset(rows_offset).limit(rows_limit if rows_limit < 501 else 1000)
        
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
                row_ordered.append(str(v))
            
            filtered_rows.append(row_ordered)
        
    except Exception:
        logger.exception("document_inspcet_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("필터링된 업무 리스트")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        return 0, 0, result
    
    return total_count, complet_count, filtered_rows


def select_log(session: Session, **kwargs: Dict) -> Union[schema.LogInfo, JSONResponse]:
    try:
        result = schema.LogInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2201)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("log select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("log")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def insert_log(
    session: Session,
    log_id: str,
    user_email: int,
    user_team: str,
    log_content: dict = {},
    auto_commit: bool = True
) -> Union[Optional[schema.LogInfo], JSONResponse]:
    try:
        result = schema.LogInfo.create(
            session=session,
            log_id=log_id,
            user_email=user_email,
            user_team=user_team,
            log_content=jsonable_encoder(log_content),
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
    try:
        result = schema.UserInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("사용자")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_user_all(session: Session, **kwargs: Dict) -> Union[List[schema.UserInfo], JSONResponse]:
    try:
        result = schema.UserInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 사용자")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_user_group_latest(session: Session, **kwargs: Dict) -> schema.UserGroup:
    dao = schema.UserGroup
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.created_time.desc()).first()
        
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user_role select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("사용자의 그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_group_info(session: Session, **kwargs: Dict) -> schema.GroupInfo:
    try:
        result = schema.GroupInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("group_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_org(session: Session, **kwargs: Dict) -> schema.KeiOrgInfo:
    try:
        result = schema.KeiOrgInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("kei_org select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("수출입은행 조직도")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_org_all(session: Session, **kwargs: Dict) -> List[schema.KeiOrgInfo]:
    try:
        result = schema.KeiOrgInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2504)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("kei_org_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 수출입은행 조직도")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def get_user_team_role(session: Session, user_email: str = "do@not.use") -> Union[Tuple[str, bool], JSONResponse]:
    # 유저의 사용자 정보 조회
    select_user_result = select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    
    # 유저의 조직 정보 (부서)
    user_team: str = select_user_result.user_team
    del select_user_result
    
    # 유저의 권한(그룹, 역할) 정보 조회
    select_user_group_result = select_user_group_latest(session, user_email=user_email)
    if isinstance(select_user_group_result, JSONResponse):
        return select_user_group_result
    
    is_admin = True if select_user_group_result.group_idx in [0 , 1] else False
    del select_user_group_result
    
    return (user_team, is_admin)