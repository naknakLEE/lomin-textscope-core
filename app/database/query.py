import json
import uuid
import traceback

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
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()


def select_cls_group(session: Session, **kwargs: Dict) -> Union[schema.ClsGroupInfo, JSONResponse]:
    try:
        result = schema.ClsGroupInfo.get(session, **kwargs)
        if result is None:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "문서 대분류 그룹")
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
        result = schema.DocTypeKvClass.get_all(session, **kwargs)
        if result is None:
            raise CoreCustomException(2108)
    except Exception:
        raise CoreCustomException(4101, "소분류와 kv class 정보")
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
            cls_idx=cls_type_idx,
            doc_type_idx=doc_type_idx,
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
        result = query.order_by(dao.inspect_end_time.desc()).first()
        
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
    cls_type_idx_list: List[int] = [],
    document_status: List[str] = [],
    document_filename: str = None,
    document_id_list: List[str] = [],
    
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
            cls_idx=cls_type_idx_list,
            user_email=uploader_list,
            document_id=document_id_list
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
        
        # 문서명 필터
        if len(document_filename) > 0:
            query = query.filter(dao_document.document_path.contains(document_filename))
        
        
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
                
                row_ordered.append(str(v))
            
            filtered_rows.append(row_ordered)
        
    except Exception:
        raise CoreCustomException(4101, "필터링된 업무 리스트")
    
    return total_count, complet_count, filtered_rows


def select_log(session: Session, **kwargs: Dict) -> Union[schema.LogInfo, JSONResponse]:
    try:
        result = schema.LogInfo.get(session, **kwargs)
        if result is None:
            status_code, error = ErrorResponse.ErrorCode.get(2201)
            result = JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    except Exception:
        raise CoreCustomException(4101, "log")
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
        session.rollback()
        raise CoreCustomException(4102, "task")
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
            raise CoreCustomException(2509)
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
