import json
import uuid

from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
from typing import Any, Dict, List, Union, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app import models
from app.database import schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import Base
from app.schemas import error_models as ErrorResponse


settings = get_settings()


def select_cls_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClsInfo], JSONResponse]:
    try:
        result = schema.ClsInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2108)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("cls_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 문서 종류(대분류)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_cls_model_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClsModel], JSONResponse]:
    try:
        result = schema.ClsModel.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2109)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("cls_model_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 문서 종류(대분류)와 모델")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_doc_type_code(session: Session, **kwargs: Dict) -> Union[str, JSONResponse]:
    try:
        result = schema.DocumentInfo.get(session, **kwargs)
        result : schema.DocumentInfo = result
        if result.doc_type_codes is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("doc_type select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("문서 종류")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result.doc_type_codes[0]

def select_doc_type(session: Session, **kwargs: Dict) -> Union[schema.DocTypeInfo, JSONResponse]:
    try:
        result = schema.DocTypeInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("doc_type select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("문서 종류(소분류)")
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
        error.error_message = error.error_message.format("모든 문서 종류(소분류)")
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


def select_class_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClassInfo], JSONResponse]:
    try:
        result = schema.ClassInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2106)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("class_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 class")
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

def select_document_doc_type(session: Session, document_id: str):
    dao_inference = schema.InferenceInfo
    dao_doc_type_info = schema.DocTypeInfo

    try:
        # get inference doc_type 
        subquery = session \
            .query(dao_inference) \
            .filter(dao_inference.document_id == document_id)\
            .subquery()
        result = session \
            .query(dao_doc_type_info) \
            .filter(dao_doc_type_info.doc_type_idx.in_(subquery))

    except:
        logger.error(f"select doc_type error")
        session.rollback()
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("등록되지 않은 doc_type")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))

    return result


def select_document_inspect_all(
    session: Session,
    ignore_upload_date: bool,
    upload_start_date: datetime,
    upload_end_date: datetime,
    ignore_inpsect_date: bool,
    inspect_start_date: datetime,
    inspect_end_date: datetime,
    date_sort_desc: bool,
    
    user_team: List[str] = [],
    uploader_list: List[str] = [],
    inspecter_list: List[str] = [],
    doc_type_idx_list: List[int] = [],
    document_status: List[str] = [],
    
    rows_limit: int = 100,
    rows_offset: int = 0,
    column_order: list = [],
) -> Union[Tuple[int, int, List[List[str]]], JSONResponse]:
    
    dao_document = schema.DocumentInfo
    dao_inspect = schema.InspectInfo
    
    try:
        # table join (inspect_id)
        query = session.query(dao_document, dao_inspect) \
            .filter(dao_document.inspect_id == dao_inspect.inspect_id)
        
        # 총 업무 개수
        if len(user_team) > 0: query = query.filter(dao_document.user_team.in_(user_team))
        total_count = query.count()
        
        # DocumentInfo 필터링
        document_filters = dict(
            # document_type=document_type,
        doc_type_idx=doc_type_idx_list,
            user_email=uploader_list
        )
        for column, filter in document_filters.items():
            if len(filter) > 0: query = query.filter(getattr(dao_document, column).in_(filter))
        
        # DocumentInfo 등록일 필터링
        if ignore_upload_date is False:
            query = query.filter(dao_document.document_upload_time.between(upload_start_date, upload_end_date))
            if date_sort_desc is True:
                query = query.order_by(dao_document.document_upload_time.desc())
            else:
                query = query.order_by(dao_document.document_upload_time.asc())
        
        
        # InsepctInfo 필터링
        inspect_filters = dict(
            user_email=inspecter_list,
            inspect_status=document_status
        )    
        for column, filter in inspect_filters.items():
            if len(filter) > 0: query = query.filter(getattr(dao_inspect, column).in_(filter))
        
        # 완료 업무 개수
        complet_count = query.filter(dao_inspect.inspect_end_time != None).count()
        
        # InspectInfo 검수 완료일 필터링
        if ignore_inpsect_date is False:
            query = query.filter(dao_inspect.inspect_end_time != None)
            query = query.filter(dao_inspect.inspect_end_time.between(inspect_start_date, inspect_end_date))
            if date_sort_desc is True:
                query = query.order_by(dao_inspect.inspect_end_time.desc())
            else:
                query = query.order_by(dao_inspect.inspect_end_time.asc())
        
        # 페이징 (한 요청당 최대 1000개)
        query = query.offset(rows_offset) \
            .limit(rows_limit if rows_limit < settings.LIMIT_SELECT_ROW + 1 else settings.LIMIT_SELECT_ROW)
        
        rows: List[Tuple[dao_document, dao_inspect]] = query.all()
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


def select_group_info_all(session: Session, **kwargs: Dict) -> List[schema.GroupInfo]:
    try:
        result = schema.GroupInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("group_info_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_company_user_info(session: Session, **kwargs: Dict) -> schema.CompanyUserInfo:
    try:
        result = schema.CompanyUserInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2524)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("company_user_info select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("사원 정보")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result

# 미사용 -> 수출입은행 관련 함수 플러그인으로 분리 예정
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

# 미사용 -> 수출입은행 관련 함수 플러그인으로 분리 예정
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

# 미사용, get_user_group_policy()대신 사용 -> 제거 예정
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


def get_inspecter_list(
    session: Session,
    user_team_list: List[str]
) -> Dict[str, str]:
    
    try:
        query = session.query(schema.DocumentInfo, schema.InspectInfo) \
            .filter(schema.DocumentInfo.user_team.in_(user_team_list)) \
            .filter(schema.DocumentInfo.inspect_id == schema.InspectInfo.inspect_id)
        
        select_inspecter_result: List[Tuple[schema.DocumentInfo, schema.InspectInfo]] = query.all()
        
        user_email_name: Dict[str, str] = dict()
        for select_result in select_inspecter_result:
            user_email_name.update(dict({select_result[1].user_email:None}))
        
        user_name_result = select_user_all(session, user_email=list(user_email_name.keys()))
        if isinstance(user_name_result, JSONResponse):
            return user_name_result
        user_name_result: List[schema.UserInfo] = user_name_result
        
        for select_result in user_name_result:
            user_email_name.update(dict({select_result.user_email:select_result.user_name}))
        
        result = user_email_name
        
    except Exception:
        logger.exception("inspecter select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("inspecter")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
        
    return result

# 순수 가지고 있는 정책(권한) 정보
# TODO 수출입은행 후 불가 정책(권한) 정보 적용 로직 추가 예정
def get_user_group_policy(
    session: Session,
    group_level: Optional[List[int]] = [],
    user_email: str = "do@not.use"
) -> Union[Dict[str, Union[bool, list]], JSONResponse]:
    
    try:
        now_datetime = datetime.now()
        
        # 사용자 정보 조회
        select_user_result = select_user(session, user_email=user_email)
        if isinstance(select_user_result, JSONResponse):
            return select_user_result
        
        user_group_policy_result: List[Tuple[schema.UserGroup, schema.GroupPolicy]]
        query = session.query(schema.UserGroup, schema.GroupPolicy) \
            .filter(schema.UserGroup.user_email == user_email) \
            .filter(schema.GroupInfo.group_code == schema.UserGroup.group_code) \
            .filter(schema.GroupInfo.group_code == schema.GroupPolicy.group_code) \
            .filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time)
        
        if len(group_level) > 0: query = query.filter(schema.GroupInfo.group_level.in_(group_level))
        
        # group_level.desc() -> 낮은 그룹 레벨 먼저 적용
        user_group_policy_result = query.order_by(schema.GroupInfo.group_level.desc()) \
            .all()
        
        # 없으면 에러 응답
        if len(user_group_policy_result) == 0:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        user_group_policy_result: List[Tuple(schema.UserGroup, schema.GroupPolicy)] = user_group_policy_result
        
        user_group_policy: Dict[str, dict] = dict()
        for policy_result in user_group_policy_result:
            
            group_policy: schema.GroupPolicy = policy_result[1]
            
            policy_code: str = group_policy.policy_code
            policy_content: dict = group_policy.policy_content
            
            # 접근 가능한 상대 팀 관련 정책
            if policy_code.endswith("_TEAM"):
                policy_content = policy_content.get("user_team", [])
                
                # user_team: List[str] = user_group_policy.get(policy_code, [])
                # user_team.extend(policy_content.get("user_team", []))
                
                # policy_content = user_team
                
            # 사용 가능한 문서 종류(대분류) 관련 정책
            elif policy_code == "R_DOC_TYPE_CLASSIFICATION":
                policy_content = policy_content.get("cls_code", [])
                
                # doc_type_big: List[str] = user_group_policy.get(policy_code, [])
                # doc_type_big.extend(policy_content.get("cls_code", []))
                
                # policy_content = doc_type_big
                
            # 사용 가능한 문서 종류(중분류) 관련 정책
            elif policy_code == "R_DOC_TYPE_SUB_CATEGORY":
                policy_content = policy_content.get("doc_type", [])
                
                # doc_type_sub: List[str] = user_group_policy.get(policy_code, [])
                # doc_type_sub.extend(policy_content.get("doc_type", []))
                
                # policy_content = doc_type_sub
                
            # 가능 여부 관련 정책
            else:
                policy_content = policy_content.get("allow", False)
            
            user_group_policy.update(dict({policy_code:policy_content}))
        result = user_group_policy
        
    except Exception:
        logger.exception("user_group_policy select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("유저 그룹 정책")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        
    return result

# user_policy에서 사용가능한 문서 종류(대분류) 정보 분리
def get_user_classification_type(session: Session, user_policy: Dict[str, Union[bool, list]]) -> List[dict]:
    # 문서 종류(대분류) 조회 (cls_code -> cls_idx)
    select_cls_result = select_cls_all(
        session,
        cls_code=list(set(user_policy.get("R_DOC_TYPE_CLASSIFICATION", [])))
    )
    if isinstance(select_cls_result, JSONResponse):
        return select_cls_result
    select_cls_result: List[schema.ClsInfo] = select_cls_result
    
    # 문서 종류(대분류)가 사용하는 cls 모델 정보 조회
    select_cls_model_result = select_cls_model_all(
        session,
        cls_idx=list(set( [ x.cls_idx for x in select_cls_result ] ))
    )
    if isinstance(select_cls_model_result, JSONResponse):
        return select_cls_model_result
    select_cls_model_result: List[schema.ClsModel] = select_cls_model_result
    
    # cls 모델 정보 조회
    select_model_result = select_model_all(
        session,
        model_idx=list(set( [ x.model_idx for x in select_cls_model_result ] ))
    )
    if isinstance(select_model_result, JSONResponse):
        return select_model_result
    select_model_result: List[schema.ModelInfo] = select_model_result
    
    # cls 모델의 문서 종류(소분류) 정보 조회
    select_class_result = select_class_all(
        session,
        model_idx=list(set( [ x.model_idx for x in select_cls_model_result ] ))
    )
    if isinstance(select_class_result, JSONResponse):
        return select_class_result
    select_class_result: List[schema.ClassInfo] = select_class_result
    
    cls_type_list: List[dict] = list()
    for cls_model_result in select_cls_model_result:
        
        cls_info: schema.ClsInfo = cls_model_result.cls_info
        model_info: schema.ModelInfo = cls_model_result.model_info
        
        docx_type_list: List[dict] = list()
        for class_result in select_class_result:
            
            if class_result.model_idx != model_info.model_idx: continue
            
            docx_type_list.append(dict(
                index   = class_result.class_idx,
                code    = class_result.class_code,
                name_kr = class_result.class_name_kr,
                name_en = class_result.class_name_en
            ))
        
        cls_type_list.append(dict(
            index         = cls_info.cls_idx,
            code          = cls_info.cls_code,
            name_kr       = cls_info.cls_name_kr,
            name_en       = cls_info.cls_name_en,
            route_name    = model_info.model_route_name,
            artifact_name = model_info.model_artifact_name,
            docx_type     = docx_type_list
        ))
    
    return cls_type_list

# user_policy에서 사용가능한 문서 종류(소분류) 정보 분리
def get_user_document_type(session: Session, user_policy: Dict[str, Union[bool, list]]) -> List[dict]:
    select_doc_type_all_result = select_doc_type_all(
        session,
        doc_type_code=list(set(user_policy.get("R_DOC_TYPE_SUB_CATEGORY", [])))
    )
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    select_doc_type_all_result: List[schema.DocTypeInfo] = select_doc_type_all_result
    
    doc_type_list: List[dict] = list()
    for result in select_doc_type_all_result:
        doc_type_list.append(dict(
            index   = result.doc_type_idx,
            code    = result.doc_type_code,
            name_kr = result.doc_type_name_kr,
            name_en = result.doc_type_name_en,
        ))
    
    return doc_type_list

