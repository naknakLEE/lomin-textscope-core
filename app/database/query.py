import json
import uuid
import traceback

from pathlib import Path
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Any, Dict, List, Union, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import nullslast, or_, func
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app import models
from app.database import schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import Base
from app.schemas import error_models as ErrorResponse
from app.middlewares.exception_handler import CoreCustomException
from datetime import datetime, timedelta

settings = get_settings()


def select_cls_group(session: Session, **kwargs: Dict) -> Union[schema.ClsGroupInfo, JSONResponse]:
    try:
        result = schema.ClsGroupInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "문서 대분류 그룹")
    return result

def select_vw_if_emp(session: Session, **kwargs: Dict)-> schema.VWIFEMP:
    try:
        result = schema.VWIFEMP.get(session, **kwargs)
    except Exception as ex:
        raise CoreCustomException(4101, "수출입은행 인사 정보")
    if result is None:
        raise CoreCustomException("C01.004.4019")
    return result
    

def select_cls_group_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClsGroupInfo], JSONResponse]:
    try:
        result = schema.ClsGroupInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "모든 문서 대분류 그룹")
    return result

def select_kv_class_info_get_all_multi(session: Session, **kwargs: Dict) -> Union[List[schema.KvClassInfo], JSONResponse]:
    try:
        result = schema.KvClassInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "모든 key value classes")
    return result

def select_doc_type_kv_class_get_all(session: Session, **kwargs: Dict) -> Union[List[schema.DocTypeKvClass], JSONResponse]:
    try:
        query = schema.DocTypeKvClass.get_all_query(session, **kwargs)
        result = query.order_by(nullslast(schema.DocTypeKvClass.sequence)).all()
        if len(result) == 0:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "소분류와 kv class 정보")
    return result

def select_rpa_form_info_get_all_latest(session: Session, **kwargs: Dict) -> Union[List[schema.RpaFormInfo], JSONResponse]:
    
    dao = schema.RpaFormInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.rpa_created_time.desc()).first()
    except Exception:
        raise CoreCustomException(4101, "rpa 템플릿 정보")
    if result is None:
        raise CoreCustomException("C01.007.4001")
    return result



def select_cls_group_model(session: Session, **kwargs: Dict) -> Union[schema.ClsGroupModel, JSONResponse]:
    try:
        result = schema.ClsGroupModel.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2108)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "문서 대분류 그룹 모델")
    return result


def select_cls_group_model_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClsGroupModel], JSONResponse]:
    try:
        result = schema.ClsGroupModel.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2109)
    except Exception:
        raise CoreCustomException(4101, "모든 문서 대분류 그룹과 모델")
    return result


def select_doc_type_cls_group_all(session: Session, **kwargs: Dict) -> Union[List[schema.DocTypeClsGroup], JSONResponse]:
    try:
        result = schema.DocTypeClsGroup.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2109)
    except Exception:
        raise CoreCustomException(4101, "모든 문서 소분류와 문서 대분류 그룹")
    return result


def select_doc_type_cls_group(session: Session, **kwargs: Dict) -> List[schema.DocTypeClsGroup]:
    try:
        result = schema.DocTypeClsGroup.get_all(session, **kwargs)
        if result is None:
            raise CoreCustomException(2109)
    except Exception:
        raise CoreCustomException(4101, "문서 소분류와 문서 대분류 그룹")
    return result

def select_doc_type(session: Session, **kwargs: Dict) -> Union[schema.DocTypeInfo, JSONResponse]:
    try:
        result = schema.DocTypeInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "문서 종류(소분류)")
    return result


def select_doc_type_all(session: Session, **kwargs: Dict) -> Union[List[schema.DocTypeInfo], JSONResponse]:
    try:
        result = schema.DocTypeInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2107)
    except Exception:
        raise CoreCustomException(4101, "모든 문서 종류(소분류)")
    return result


def select_doc_type_kv_class(session: Session, **kwargs: Dict) -> Union[List[schema.DocTypeKvClass], JSONResponse]:
    try:
        result = schema.DocTypeKvClass.get_all(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2107)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("doc_type_kv_class_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 문서 종류(소분류)와 kv class")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return result


def select_model(session: Session, **kwargs: Dict) -> Union[schema.ModelInfo, JSONResponse]:
    try:
        result = schema.ModelInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2106)
    except Exception:
        raise CoreCustomException(4101, "모델")
    return result


def select_model_all(session: Session, **kwargs: Dict) -> Union[List[schema.ModelInfo], JSONResponse]:
    try:
        result = schema.ModelInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2106)
    except Exception:
        raise CoreCustomException(4101, "모든 모델")
    return result


def select_class_all(session: Session, **kwargs: Dict) -> Union[List[schema.ClassInfo], JSONResponse]:
    try:
        result = schema.ClassInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2106)
    except Exception:
        raise CoreCustomException(4101, "모든 class")
    return result


def select_document(session: Session, **kwargs: Dict) -> Union[schema.DocumentInfo, JSONResponse]:
    try:
        result = schema.DocumentInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2101)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "문서")
    return result


def select_document_all(session: Session, **kwargs: Dict) -> Union[List[schema.DocumentInfo], JSONResponse]:
    try:
        query = schema.DocumentInfo.get_all_query_multi(session, **kwargs)
        result = query.order_by(schema.DocumentInfo.document_upload_time.asc()).all()
        if len(result) == 0:
            raise CoreCustomException(2101)
    except Exception:
        raise CoreCustomException(4101, "모든 문서")
    return result


def get_prev_next_documnet_id(
    session: Session,
    document_id: str,
    user_team: List[str],
    cls_idx: List[int]
) -> dict:
    try:
        try:
            document_upload_date = session.query(schema.DocumentInfo) \
                .filter(schema.DocumentInfo.document_id == document_id) \
                .first().document_upload_time
        except Exception:
            raise CoreCustomException(2101)
        
        prev_document = session.query(schema.DocumentInfo) \
            .filter(schema.DocumentInfo.is_used == True) \
            .filter(schema.DocumentInfo.user_team.in_(user_team)) \
            .filter(schema.DocumentInfo.cls_idx.in_(cls_idx)) \
            .filter(schema.DocumentInfo.document_upload_time < document_upload_date) \
            .order_by(schema.DocumentInfo.document_upload_time.desc()) \
            .first()
        
        next_document = session.query(schema.DocumentInfo) \
            .filter(schema.DocumentInfo.is_used == True) \
            .filter(schema.DocumentInfo.user_team.in_(user_team)) \
            .filter(schema.DocumentInfo.cls_idx.in_(cls_idx)) \
            .filter(schema.DocumentInfo.document_upload_time > document_upload_date) \
            .order_by(schema.DocumentInfo.document_upload_time.asc()) \
            .first()
        
    except CoreCustomException as cce:
        raise cce
    except Exception:
        raise CoreCustomException(4101, "모든 문서")
    
    return {
        "prev":prev_document.document_id if prev_document is not None else "None",
        "now":document_id,
        "next":next_document.document_id if next_document is not None else "None"
    }


def insert_document(
    session: Session,
    user_email: int,
    user_team: str,
    document_path: str,
    document_id: str = str(uuid.uuid4()),
    document_description: Optional[str] = None,
    document_type: str = "TRAINING",
    document_pages: int = 0,
    cls_type_idx: int = 0,
    doc_type_idx: List[int] = [0],
    doc_type_code: List[str] = ["GOCR"],
    is_used: bool = True,
    auto_commit: bool = True
) -> Optional[schema.DocumentInfo]:
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
            cls_idx=cls_type_idx,
            doc_type_idx=doc_type_idx,
            doc_type_code=doc_type_code,
            is_used=is_used,
            auto_commit=auto_commit,
        )
    except Exception:
        session.rollback()
        raise CoreCustomException(4102, "문서")
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
        session.rollback()
        raise CoreCustomException(4102, "문서")
    return result


def select_inference_latest(session: Session, **kwargs: Dict) -> schema.InferenceInfo:
    dao = schema.InferenceInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.inference_end_time.desc()).first()
        
        if result is None:
            raise CoreCustomException(2507)
    except Exception:
        raise CoreCustomException(4101, "최근 추론")
    return result

def select_inference_all(session: Session, **kwargs: Dict) -> Union[List[schema.InferenceInfo], JSONResponse]:
    dao = schema.InferenceInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.inference_end_time.desc()).all()
        
        if result is None:
            raise CoreCustomException(2507)
    except Exception:
        raise CoreCustomException(4101, "최근 추론")
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
        session.rollback()
        
        raise CoreCustomException(4102, "추론")
    return result


def select_inspect_latest(session: Session, **kwargs: Dict) -> Union[schema.InspectInfo, JSONResponse]:
    dao = schema.InspectInfo
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.inspect_start_time.desc()).first()
        
    except Exception:
        raise CoreCustomException(4101, "가장 최근 검수")
    return result


def insert_inspect(session: Session, **kwargs: Dict) -> Union[Optional[schema.InspectInfo], JSONResponse]:
    try:
        result = schema.InspectInfo.create(session=session, **kwargs)
    except Exception:
        session.rollback()
        raise CoreCustomException(4102, "추론")
    return result

def insert_rpa_form_info(session: Session, **kwargs: Dict) -> Union[Optional[schema.RpaFormInfo], JSONResponse]:
    try:
        result = schema.RpaFormInfo.create(session=session, **kwargs)
    except Exception:
        session.rollback()
        raise CoreCustomException(4102, "rpa 템플릿")
    return result


def select_document_inspect_all(
    session: Session,
    upload_start_date: datetime,
    upload_end_date: datetime,
    inspect_start_date: datetime,
    inspect_end_date: datetime,
    upload_date: bool,
    date_sort_desc: bool,
    upload_date_sort: bool,
    
    user_team: List[str] = [],
    uploader_list: List[str] = [],
    inspecter_list: List[str] = [],
    doc_type_idx_list: List[int] = [],
    document_status: List[str] = [],
    document_filename: str = None,
    document_id_list: List[str] = [],
    
    rows_limit: int = 100,
    rows_offset: int = 0,
    column_order: list = [],
) -> Union[Tuple[int, int, int, List[List[str]]], JSONResponse]:
    
    dao_document = schema.DocumentInfo
    dao_inspect = schema.InspectInfo
    
    try:
        # table join (inspect_id)
        query = session.query(dao_document, dao_inspect) \
            .filter(dao_document.is_used == True) \
            .filter(dao_document.inspect_id == dao_inspect.inspect_id)
        
        if len(user_team) > 0: query = query.filter(dao_document.user_team.in_(user_team))
        
        # DocumentInfo 필터링
        document_filters = dict(
            user_email=uploader_list,
            document_id=document_id_list
        )
        for column, filter in document_filters.items():
            if len(filter) > 0: query = query.filter(getattr(dao_document, column).in_(filter))
        
        # 문서의 첫번째 이미지 문서 종류(소분류) 필터링
        if len(doc_type_idx_list) > 0:
            query = query.filter(dao_document.doc_type_cls_match[0].in_(doc_type_idx_list))
        
        # InsepctInfo 필터링
        inspect_filters = dict(
            user_email=inspecter_list,
            inspect_status=document_status
        )    
        for column, filter in inspect_filters.items():
            if len(filter) > 0: query = query.filter(getattr(dao_inspect, column).in_(filter))
        
        # DocumentInfo 등록일 기간 필터링
        if upload_date:
            query = query.filter(dao_document.document_upload_time.between(upload_start_date, upload_end_date))
        # InspectInfo 검수 완료일 기간 필터링
        elif upload_date is False:
            query = query.filter(dao_inspect.inspect_end_time != None)
            query = query.filter(dao_inspect.inspect_end_time.between(inspect_start_date, inspect_end_date))
        
        # 정렬 방법
        if upload_date_sort is True:
            if date_sort_desc is True:
                query = query.order_by(dao_document.document_upload_time.desc())
            else:
                query = query.order_by(dao_document.document_upload_time.asc())
        else:
            if date_sort_desc is True:
                query = query.order_by(nullslast(dao_inspect.inspect_end_time.desc()))
            else:
                query = query.order_by(nullslast(dao_inspect.inspect_end_time.asc()))
        
        # 문서명 필터
        if len(document_filename) > 0:
            query = query.filter(dao_document.document_path.contains(document_filename))
        
        filtered_count = query.count()
        complet_count = query.filter(dao_inspect.inspect_status == "INSPECTED").count()
        
        # 페이징 (한 요청당 최대 1000개)
        query = query.offset(rows_offset) \
            .limit(rows_limit if rows_limit < settings.LIMIT_SELECT_ROW + 1 else settings.LIMIT_SELECT_ROW)
        
        rows: List[Tuple[dao_document, dao_inspect]] = query.all()
        filtered_rows = list()
        table_mapping = {
            "DocumentInfo": None,
            "InspectInfo": None,
        }
        
        for row in rows:
            table_mapping.update(DocumentInfo=row[0])
            table_mapping.update(InspectInfo=row[1])
            
            row_ordered: list = list()
            for table_column in column_order:
                tc = table_column.split(".")
                
                v = table_mapping.get(tc[0])
                for i in range(1, len(tc)):
                    v = getattr(v, tc[i], "None")
                
                row_ordered.append(v)
            
            filtered_rows.append(row_ordered)
        
        
    except Exception:
        raise CoreCustomException(4101, "필터링된 업무 리스트")
    
    return filtered_count, complet_count, filtered_count, filtered_rows


def get_log_all_by_created_time(
    session: Session,
    authority_date_start,
    authority_date_end,
    **kwargs: Dict
) -> List[schema.LogInfo]:
    try:
        result = schema.LogInfo.get_all_query(session, **kwargs) \
            .filter(schema.LogInfo.created_time.between(authority_date_start, authority_date_end)) \
            .order_by(schema.LogInfo.created_time.desc()) \
            .all()
    except Exception:
        raise CoreCustomException(4101, "모든 로그")
    return result


def select_log_all(session: Session, **kwargs: Dict) -> Union[List[schema.LogInfo], JSONResponse]:
    try:
        result = schema.LogInfo.get_all(session, **kwargs)
        if len(result) == 0:
            status_code, error = ErrorResponse.ErrorCode.get(2201)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "모든 로그")
    return result


def select_log(session: Session, **kwargs: Dict) -> Union[schema.LogInfo, JSONResponse]:
    try:
        result = schema.LogInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2201)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "로그")
    return result


def insert_log(
    session: Session,
    log_id: str,
    log_type: str,
    user_email: int,
    user_team: str,
    log_content: dict = {},
    auto_commit: bool = True
) -> Optional[schema.LogInfo]:
    try:
        result = schema.LogInfo.create(
            session=session,
            log_id=log_id,
            log_type=log_type,
            user_email=user_email,
            user_team=user_team,
            log_content=jsonable_encoder(log_content),
            auto_commit=auto_commit
        )
    except Exception:
        session.rollback()
        raise CoreCustomException(4102, "로그")
    return result


def select_user(session: Session, **kwargs: Dict) -> schema.UserInfo:
    try:
        result = schema.UserInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2504)
    except Exception:
        raise CoreCustomException(4101, "사용자")
    return result


def select_user_all(session: Session, **kwargs: Dict) -> Union[List[schema.UserInfo], JSONResponse]:
    try:
        result = schema.UserInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2101)
    except Exception:
        raise CoreCustomException(4101, "모든 사용자")
    return result


def select_user_group_all(session: Session, **kwargs: Dict) -> Union[List[schema.UserGroup], JSONResponse]:
    dao = schema.UserGroup
    try:
        result = dao.get_all(session, **kwargs)
        
        if result is None:
            raise CoreCustomException(2509)
    except Exception:
        raise CoreCustomException(4101, "모든 사용자의 그룹(권한, 역할)")
    return result


def select_user_group_all_multi(session: Session, **kwargs: Dict) -> Union[List[schema.UserGroup], JSONResponse]:
    dao = schema.UserGroup
    try:
        result = dao.get_all_multi(session, **kwargs)
        
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("user_group_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 사용자의 그룹(권한, 역할)")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_user_group_latest(session: Session, **kwargs: Dict) -> Union[schema.UserGroup, JSONResponse]:
    dao = schema.UserGroup
    try:
        query = dao.get_all_query(session, **kwargs)
        result = query.order_by(dao.created_time.desc()).first()
        
        if result is None:
            raise CoreCustomException(2509)
    except Exception:
        raise CoreCustomException(4101, "사용자의 그룹(권한, 역할)")
    return result


def select_group_info(session: Session, **kwargs: Dict) -> schema.GroupInfo:
    try:
        result = schema.GroupInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2509)
    except Exception:
        raise CoreCustomException(4101, "그룹(권한, 역할)")
    return result


def select_group_info_all(session: Session, **kwargs: Dict) -> List[schema.GroupInfo]:
    try:
        result = schema.GroupInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2509)
    except Exception:
        raise CoreCustomException(4101, "모든 그룹(권한, 역할)")
    return result


def select_company_user_info(session: Session, **kwargs: Dict) -> Union[schema.CompanyUserInfo, JSONResponse]:
    try:
        result = schema.CompanyUserInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2524)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "사원 정보")
    return result


def select_company_user_info_all(session: Session, **kwargs: Dict) -> Union[schema.CompanyUserInfo, JSONResponse]:
    try:
        result = schema.CompanyUserInfo.get_all_multi(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2524)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        logger.exception("company_user_info_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 사원 정보")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return result


def select_company_user_info_query(session: Session, search_text: str, **kwargs: Dict) -> Union[Tuple[int, List[schema.CompanyUserInfo]], JSONResponse]:
    dao = schema.CompanyUserInfo
    total_count = 0
    try:
        query = dao.get_all_query(session, **kwargs)
        query = query.filter(dao.emp_fst_rgst_dttm != None)
        
        total_count = query.count()
        
        result = query.filter(
            or_(
                dao.emp_eno.contains(search_text),
                dao.emp_usr_nm.contains(search_text),
                # dao.emp_usr_emad.contains(search_text),
                
                # dao.emp_usr_mpno.contains(search_text),
                # dao.emp_org_path.contains(search_text)
            )
        ) \
        .order_by(dao.emp_eno.asc()) \
        .all()
    except Exception:
        logger.exception("company_user_info_all select error")
        status_code, error = ErrorResponse.ErrorCode.get(4101)
        error.error_message = error.error_message.format("모든 사원 정보")
        result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))
    return total_count, result

# 미사용 -> 수출입은행 관련 함수 플러그인으로 분리 예정
def select_org(session: Session, **kwargs: Dict) -> schema.KeiOrgInfo:
    try:
        result = schema.KeiOrgInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2504)
    except Exception:
        raise CoreCustomException(4101, "수출입은행 조직도")
    return result

# 미사용 -> 수출입은행 관련 함수 플러그인으로 분리 예정
def select_org_all(session: Session, **kwargs: Dict) -> List[schema.KeiOrgInfo]:
    try:
        result = schema.KeiOrgInfo.get_all_multi(session, **kwargs)
        if result is None:
            raise CoreCustomException(2504)
    except Exception:
        raise CoreCustomException(4101, "모든 수출입은행 조직도")
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
    inspecter_list: List[str]
) -> Dict[str, str]:
    
    try:
        query = session.query(schema.DocumentInfo, schema.InspectInfo) \
            .filter(schema.DocumentInfo.user_email.in_(inspecter_list)) \
            .filter(schema.DocumentInfo.inspect_id == schema.InspectInfo.inspect_id)
        
        select_inspecter_result: List[Tuple[schema.DocumentInfo, schema.InspectInfo]] = query.all()
        
        user_email_info: Dict[str, schema.UserInfo] = dict()
        for select_result in select_inspecter_result:
            user_email_info.update(dict({select_result[1].user_email:None}))
        
        user_name_result = select_user_all(session, user_email=list(user_email_info.keys()))
        if isinstance(user_name_result, JSONResponse):
            return user_name_result
        user_name_result: List[schema.UserInfo] = user_name_result
        
        for user_info in user_name_result:
            user_email_info.update(dict({user_info.user_email:user_info}))
        
        result = user_email_info
        
    except Exception:
        raise CoreCustomException(4101, "inspecter")
        
    return result

# 개인 권한 적용 기간 조회
def get_user_policy_time(session: Session, user_email: str = "do@not.use", authrotiy: str = "없음") -> dict:
    try:
        now_datetime = datetime.now()
        
        user_group_policy_result: List[schema.GroupPolicy]
        query = session.query(schema.GroupPolicy) \
            .filter(schema.GroupPolicy.group_code == user_email) \
            .filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time) \
        
        user_group_policy_result = query.all()
        
        # 없으면 최대 1년 기간 설정
        if len(user_group_policy_result) == 0:
            return {
                "start_time":datetime.now(),
                "end_time":datetime.now() + timedelta(days=365),
            }
        
        user_group_policy: Dict[str, schema.GroupPolicy] = dict()
        user_group_policy = { x.policy_code : x for x in user_group_policy_result }
        
        start_time = None
        end_time = None
        if authrotiy == "관리자":
            start_time = user_group_policy.get("C_GRANT_ADMIN").start_time
            end_time = user_group_policy.get("C_GRANT_ADMIN").end_time
        else:
            start_time = user_group_policy.get("R_DOCX_TEAM").start_time
            end_time = user_group_policy.get("R_DOCX_TEAM").end_time
        
    except Exception:
        raise CoreCustomException(4101, "유저 정책")
        
    return {
        "start_time":start_time,
        "end_time":end_time
    }


def get_user_authority(user_policy_result: Dict[str, Union[bool, list]]) -> str:
    authority = "없음"
    
    admin = True
    for admin_code in settings.ADMIN_POLICY:
        if admin_code not in user_policy_result.keys(): admin = False
        v = user_policy_result.get(admin_code)
        if isinstance(v, bool): admin &= v
    
    if admin is True:
        authority = "관리자"
    elif len(user_policy_result.get("R_DOCX_TEAM", [])) > 0:
        authority = "일반"
    else:
        authority = "없음"
    
    return authority


def select_group_policy(session: Session, group_code: str = "NO_CODE") -> Union[List[schema.GroupPolicy], JSONResponse]:
    try:
        result = schema.GroupPolicy.get_all(
            session=session,
            group_code=group_code
        )
        if len(result) == 0:
            raise CoreCustomException(2509)
    except CoreCustomException as cce:
        raise cce
    except Exception:
        raise CoreCustomException(4102, "사용자 권한")
    return result


def upsert_user_group_policy(
    session: Session,
    group_code: str = "0000_0000",
    policy_code: str = "NO_CODE",
    policy_content: dict = {},
    authority_time_start: datetime = datetime.now(),
    authority_time_end:   datetime = datetime.now() + timedelta(days=30),
    auto_commit: bool = True
) -> Union[Optional[schema.GroupPolicy], JSONResponse]:
    try:
        query: schema.GroupPolicy = session.query(schema.GroupPolicy) \
            .filter(schema.GroupPolicy.group_code == group_code) \
            .filter(schema.GroupPolicy.policy_code == policy_code) \
            .first()
        
        if query is not None:
            query.group_code = group_code
            query.policy_code = policy_code
            query.policy_content = policy_content
            query.start_time = authority_time_start
            query.end_time = authority_time_end
            
        elif query is None:
            query = schema.GroupPolicy(
                group_code=group_code,
                policy_code=policy_code,
                policy_content=policy_content,
                start_time=authority_time_start,
                end_time=authority_time_end
            )
            session.add(query)
            
        session.commit()
        
    except Exception:
        raise CoreCustomException(4102, "사용자 권한")
    return query


def delete_user_group_policy(
    session: Session,
    group_code: str = "0000_0000",
    policy_code: str = "NO_CODE",
    auto_commit: bool = True
) -> None:
    try:
        query = session.query(schema.GroupPolicy) \
            .filter(schema.GroupPolicy.group_code == group_code) \
            .filter(schema.GroupPolicy.policy_code == policy_code) \
            .first()
        
        if query is not None:
            session.delete(query)
            session.commit()
        
    except Exception:
        raise CoreCustomException("D01.900.5003", "사용자 권한")
    return query


# 순수 가지고 있는 정책(권한) 정보
# TODO 아래 get_user_group_policy의 성능상 문제로 추후 합칠 예정
def get_user_group_policy_all(
    session: Session,
    group_level: Optional[List[int]] = [],
    user_email_list: List[str] = ["do@not.use"]
) -> Union[Dict[str, Dict[str, Union[bool, list]]], JSONResponse]:
    try:
        now_datetime = datetime.now()
        
        all_user_group_result: List[Tuple[schema.UserGroup, schema.GroupInfo, schema.GroupPolicy]] = list()
        query = session.query(schema.UserGroup, schema.GroupInfo, schema.GroupPolicy)
        query = query.filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time)
        query = query.filter(schema.UserGroup.group_code == schema.GroupInfo.group_code, schema.UserGroup.group_code == schema.GroupPolicy.group_code)
        query = query.filter(schema.UserGroup.user_email.in_(user_email_list))
        if len(group_level) > 0: query = query.filter(schema.GroupInfo.group_level.in_(group_level))
        # group_level.desc() -> 낮은 그룹 레벨 먼저 적용
        all_user_group_result = query.order_by(schema.GroupInfo.group_level.desc()).all()
        
        # user_email이 포함된 group중 가장 level이 높은 그룹의 level을 가져옴
        all_highest_lvl_group: Dict[str, int] = dict()
        query = session.query(schema.UserGroup.user_email, func.min(schema.GroupInfo.group_level))
        query = query.filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time)
        query = query.filter(schema.UserGroup.group_code == schema.GroupInfo.group_code, schema.UserGroup.group_code == schema.GroupPolicy.group_code)
        query = query.filter(schema.UserGroup.user_email.in_(user_email_list))
        if len(group_level) > 0: query = query.filter(schema.GroupInfo.group_level.in_(group_level))
        all_highest_lvl_group = { _[0]:_[1] for _ in query.group_by(schema.UserGroup.user_email).all() }
        
        # 없으면 에러 응답
        # if len(all_user_group_result) == 0:
        #     raise CoreCustomException(2509)
        
        all_user_group_policy: Dict[str, Dict[str, Union[bool, list]]] = dict()
        for user_group_policy in all_user_group_result:
            user_group, group_info, group_policy = user_group_policy
            
            if group_info.group_level != all_highest_lvl_group.get(user_group.user_email): continue
            
            policy_code: str = group_policy.policy_code
            policy_content: dict = group_policy.policy_content
            
            # 접근 가능한 상대 팀 관련 정책
            if policy_code.endswith("_TEAM"):
                policy_content = policy_content.get("user_team", [])
                
            # 사용 가능한 문서 종류(대분류) 관련 정책
            elif policy_code == "R_DOC_TYPE_CLASSIFICATION":
                policy_content = policy_content.get("cls_code", [])
                
            # 사용 가능한 문서 종류(중분류) 관련 정책
            elif policy_code == "R_DOC_TYPE_SUB_CATEGORY":
                policy_content = policy_content.get("doc_type", [])
                
            # 가능 여부 관련 정책
            else:
                policy_content = policy_content.get("allow", False)
            
            user_policy = all_user_group_policy.get(user_group.user_email, {})
            user_policy.update({policy_code:policy_content})
            all_user_group_policy.update({user_group.user_email:user_policy})
        
        result = all_user_group_policy
        
    except CoreCustomException as cce:
        raise cce
    except Exception:
        raise CoreCustomException(4101, "모든 유저 그룹 정책")
    
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
        
        select_user_group_result: List[schema.UserGroup] = select_user_group_all(session, user_email=user_email)
        group_list: List[str] = [ x.group_code for x in select_user_group_result ]
        
        user_group_policy_result: List[Tuple[schema.GroupInfo, schema.GroupPolicy]] = list()
        query = session.query(schema.GroupInfo, schema.GroupPolicy)
        query = query.filter(schema.GroupInfo.group_code.in_(group_list))
        query = query.filter(schema.GroupInfo.group_code == schema.GroupPolicy.group_code)
        query = query.filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time)
        if len(group_level) > 0: query = query.filter(schema.GroupInfo.group_level.in_(group_level))
        # group_level.desc() -> 낮은 그룹 레벨 먼저 적용
        user_group_policy_result = query.order_by(schema.GroupInfo.group_level.desc()).all()
        
        # user_email이 포함된 group중 가장 level이 높은 그룹의 level을 가져옴
        all_highest_lvl_group: Dict[str, int] = dict()
        query = session.query(schema.UserGroup.user_email, func.min(schema.GroupInfo.group_level))
        query = query.filter(schema.GroupPolicy.start_time < now_datetime, now_datetime < schema.GroupPolicy.end_time)
        query = query.filter(schema.UserGroup.group_code == schema.GroupInfo.group_code, schema.UserGroup.group_code == schema.GroupPolicy.group_code)
        query = query.filter(schema.UserGroup.user_email == user_email)
        if len(group_level) > 0: query = query.filter(schema.GroupInfo.group_level.in_(group_level))
        all_highest_lvl_group = { _[0]:_[1] for _ in query.group_by(schema.UserGroup.user_email).all() }
        
        # 없으면 에러 응답
        if len(user_group_policy_result) == 0:
            raise CoreCustomException(2509)
        user_group_policy_result: List[Tuple(schema.UserGroup, schema.GroupPolicy)] = user_group_policy_result
        
        user_group_policy: Dict[str, dict] = dict()
        for policy_result in user_group_policy_result:
            group_info, group_policy = policy_result
            
            if group_info.group_level != all_highest_lvl_group.get(user_email): continue
            
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
    except CoreCustomException as cce:
        raise cce
    except Exception:
        raise CoreCustomException(4101, "유저 그룹 정책")
    
    return result

# user_policy에서 사용가능한 문서 대분류 그룹 정보 분리
def get_user_classification_type(session: Session, cls_code_list: List[str]) -> List[dict]:
    # 문서 대분류 그룹 정보 조회 (cls_code -> cls_idx)
    select_cls_result = select_cls_group_all(session, cls_code=cls_code_list)
    if isinstance(select_cls_result, JSONResponse):
        return select_cls_result
    select_cls_result: List[schema.ClsGroupInfo] = select_cls_result
    
    # 문서 대분류 그룹이 가지는 문서 종류(소분류) 목록 조회
    select_doc_type_cls_group_result = select_doc_type_cls_group_all(
        session,
        cls_idx=list(set( [ x.cls_idx for x in select_cls_result ] ))
    )
    if isinstance(select_doc_type_cls_group_result, JSONResponse):
        return select_doc_type_cls_group_result
    select_doc_type_cls_group_result: List[schema.DocTypeClsGroup] = select_doc_type_cls_group_result
    
    # 문서 대분류 그룹이 사용하는 cls 모델 정보 조회
    select_cls_group_model_result = select_cls_group_model_all(
        session,
        cls_idx=list(set( [ x.cls_idx for x in select_cls_result ] ))
    )
    if isinstance(select_cls_group_model_result, JSONResponse):
        return select_cls_group_model_result
    select_cls_group_model_result: List[schema.ClsGroupModel] = select_cls_group_model_result
    
    # 문서 대분류 그룹과 cls 모델 정보 매핑
    cls_group_model_map: Dict[int, schema.ModelInfo] = dict()
    for select_cls_group_model in select_cls_group_model_result:
        cls_group_model_map.update({select_cls_group_model.cls_idx:select_cls_group_model.model_info})
    
    cls_group_map: Dict[int, schema.ClsGroupInfo] = dict()
    cls_group_doc_type_map: Dict[int, List[dict]] = dict()
    for select_doc_type_cls_group in select_doc_type_cls_group_result:
        cls_group_info: schema.ClsGroupInfo = select_doc_type_cls_group.cls_group_info
        doc_type_info: schema.DocTypeInfo = select_doc_type_cls_group.doc_type_info
        
        cls_group_map.update({cls_group_info.cls_idx:cls_group_info})
        
        befor_doc_type_info_list = cls_group_doc_type_map.get(cls_group_info.cls_idx, [])
        befor_doc_type_info_list.append(dict(
            index=doc_type_info.doc_type_idx,
            code=doc_type_info.doc_type_code,
            name_kr=doc_type_info.doc_type_name_kr,
            name_en=doc_type_info.doc_type_name_en
        ))
        
        cls_group_doc_type_map.update({cls_group_info.cls_idx:befor_doc_type_info_list})
    
    cls_type_list: List[dict] = list()
    for cls_idx, cls_group_info in cls_group_map.items():
        
        cls_model_info: schema.ModelInfo = cls_group_model_map.get(cls_idx)
        
        cls_type_list.append(dict(
            index=cls_group_info.cls_idx,
            code=cls_group_info.cls_code,
            name_kr=cls_group_info.cls_name_kr,
            name_en=cls_group_info.cls_name_en,
            route_name=cls_model_info.model_route_name if cls_model_info else None,
            artifact_name=cls_model_info.model_artifact_name if cls_model_info else None,
            docx_type=cls_group_doc_type_map.get(cls_group_info.cls_idx, {})
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



def select_api_log_all(
    session: Session,
    **kwargs
) -> Tuple[dict, dict]:          
    """
        [Front]전용 대시보드 정보 조회
    """
    query_param: Dict = dict(kwargs)
    date_end_after_one_day = datetime.strptime(kwargs.get('date_end'), '%Y.%m.%d') + timedelta(1)
    date_end_after_one_day = date_end_after_one_day.strftime('%Y.%m.%d')

    query_param.update(
        date_end=date_end_after_one_day
    )

    sql_select_api_log_all = \
        """
        select to_char(api_response_datetime,'YYYY-MM-DD') as date,
            avg(cast(api_response_time as real)) as avg_speed_value,
            count(case when api_is_success is true then 1 end) as success_count,
            count(case when api_is_success is false then 1 end) as fail_count,
            count(*) as total_count
        from log_api
        where api_response_datetime between :date_start and :date_end
        group by to_char(api_response_datetime,'YYYY-MM-DD');    
        """

    result = session.execute(
        sql_select_api_log_all,
        query_param
    )    
    
    processing_mapping_keys = ['success_count', 'fail_count']
    speed_mapping_keys = ['avg_speed_value']

    processing_list = list()
    speed_list = list()

    processing_total_dict = {
        'total_success_count': 0,
        'total_fail_count': 0
    }
    min_speed_value = 9999
    max_speed_value = 0
    for rowproxy in result:
        processing_dict = dict()
        speed_dict = dict()        
        for column, value in rowproxy.items():
            if(column == 'date'):
                processing_dict.update({
                    column: value
                })                
                speed_dict.update({
                    column: value
                })                
            elif(column in processing_mapping_keys):
                processing_dict.update({
                    column: value
                })
                processing_total_dict.update({
                    f'total_{column}': processing_total_dict.get(f'total_{column}') + value
                })
            elif(column in speed_mapping_keys):
                speed_dict.update({
                    column: value
                })
                if min_speed_value > value: min_speed_value = value
                if max_speed_value < value: max_speed_value = value               
        processing_list.append(processing_dict)                                
        speed_list.append(speed_dict)

    if min_speed_value == 9999: min_speed_value = 0 

    speed_total_dict = {
        'min_speed_value': min_speed_value if min_speed_value != 9999 else 0,
        'max_speed_value': max_speed_value,
        'avg_speed_value': (min_speed_value + max_speed_value) / 2,
        'daily_response_speed_list': speed_list
    }        
    processing_total_dict.update({
        'total_call_count': sum(processing_total_dict.values()),
        'daily_processing_status_list': processing_list 
    })
    return speed_total_dict, processing_total_dict

def delete_nak_data(
    session: Session,
    date_time_str: str,
):
    """
        document_info table delete
    """
    result = False 
    try:
        document_info = schema.DocumentInfo
        # 0. 검수작업 하지 않은 document_info 가져오기          
        document_get_do_not_update_query = session.query(schema.DocumentInfo).filter(
            func.to_char(document_info.document_upload_time, 'YYYY-mm-dd') == date_time_str,
            document_info.inspect_id == "NOT_INSPECTED"
            )
        do_not_update_list = document_get_do_not_update_query.all()
        do_not_update_path_list = list()
        for do_not_update_info in do_not_update_list:
            origin_document_name = do_not_update_info.document_path.split("/")[-1]
            document_regist_date:str = str(do_not_update_info.document_path)[:10]
            real_docx_id = "/".join([document_regist_date, do_not_update_info.document_id, origin_document_name])
            do_not_update_path_list.append(real_docx_id)

        # 1. inspect_info 삭제 -> cascade가 recursive하게 되지 않음
        # TODO: cascade로 삭제할 수 있게 처리하기
        sql_inspect_info_delete_query = \
            """
                delete 
                from inspect_info
                where inspect_id in (
                    select ii.inspect_id
                    from inspect_info ii
                    join inference_info ii2 on ii.inference_id  = ii2.inference_id
                    join document_info di on ii2.document_id = di.document_id
                    where to_char(di.document_upload_time, 'YYYY-mm-dd') = :date_time_str
                    );            
            """
        session.execute(
            sql_inspect_info_delete_query,
            dict(
                date_time_str=date_time_str
            )
        )            
        # 2. document_info 삭제
        document_info = schema.DocumentInfo
        document_info_delete_query = session.query(schema.DocumentInfo).filter(func.to_char(document_info.document_upload_time, 'YYYY-mm-dd') == date_time_str)
        logger.debug(f">>>>>>>>>>>>>>>>>> delete document_info count:{document_info_delete_query.count()}" )
        document_info_delete_query.delete(synchronize_session=False)
        session.commit()
        result = do_not_update_path_list
    except Exception as exc:
        logger.error(exc, exc_info=True)
        session.rollback()
        raise CoreCustomException("D01.900.5003", "document_info")        
    finally:
        session.flush()
        return result

def update_log_api_fail(session: Session, api_id: str, **kwargs: Dict) -> Union[Optional[schema.DocumentInfo], JSONResponse]:
    try:
        result = schema.LogAPI.update(
            session=session,
            p_key="api_id",
            p_value=api_id,
            **kwargs
        )
    except Exception as exc:
        logger.error(exc, exc_info=True)
        session.rollback()
        raise CoreCustomException(4102, "문서")
    return result        