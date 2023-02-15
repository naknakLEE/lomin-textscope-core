from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set
from fastapi import APIRouter, Depends, Body, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import db
from app.database import query, schema
from app.common.const import settings
from app.utils.logging import logger
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.utils.image import (
    read_image_from_bytes,
    get_image_bytes,
    image_to_base64,
)
from app.utils.utils import is_admin
from app.service.document import (
    get_thumbnail as get_thumbnail_service,
    get_filter_user as get_filter_user_service,
    get_filter_department as get_filter_department_service,
    get_filter_cls_type as get_filter_cls_type_service,
    get_filter_doc_type as get_filter_doc_type_service,
    get_document_list as get_document_list_service,
    get_document_inference_info as get_document_inference_info_service
    )
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


@router.get("/thumbnail")
def get_thumbnail(
    document_id:  str,
    page_num:     int             = 0,
    scale:        float           = 0.4,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 문서 썸네일 확인
    """
    return get_thumbnail_service(
        document_id = document_id,
        page_num = page_num,
        scale = scale,
        current_user = current_user,
        session = session
    )


@router.get("/filter/user")
def get_filter_user(
    user_team:    str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 업무 리스트 필터링시 조회 가능한 등록자, 검수자 목록 조회
    """
    return get_filter_user_service(
        user_team = user_team,
        current_user = current_user,
        session = session
    )
    


@router.get("/filter/department")
def get_filter_department(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 조회 가능한 부서(=그룹.그룹코드) = user_team(=group_info.group_code) 목록 조회
    """
    return get_filter_department_service(
        current_user = current_user,
        session = session
    )


@router.get("/filter/cls-type")
def get_filter_cls_type(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 사용가능한 문서 종류(대분류) 목록 조회
    """
    return get_filter_cls_type_service(
        current_user = current_user,
        session = session
    )


@router.get("/filter/docx-type")
def get_filter_doc_type(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 사용가능한 문서 종류(소분류) 목록 조회
    """
    return get_filter_doc_type_service(
        current_user = current_user,
        session = session
    )


@router.post("/list")
def get_document_list(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링 및 페이징
    1. user_email에 따른 권한(정책) 정보를 가져옵니다. -> [# 사용자의 모든 정책(권한) 확인]
        1-1. 요청한 그룹이 조회 가능한 그룹에 없을 경우 에러 응답을 반환합니다. -> [# 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 반환]
    2. 사용자가 요청한 문서 종류가 조회가능한 문서 종류인지 비교합니다. -> [# 사용자 정책(조회 가능 문서 종류) 확인]
        2-1. 요청한 그룹이 조회 가능한 그룹에 없을 경우 에러 응답을 반환합니다. -> [# 요청한 문서 종류가 조회 가능한 문서 목록에 없을 경우 에러 반환]
    3. 등록일 또는 검수일 기간 파싱 -> [# 등록일, 검수일 기간 파싱]
        2-1. 등록 기간 파싱 실패를 전체 등록일 기간으로 간주합니다.
        2-2. 검수 기간 파싱 실패를 전체 검수일 기간으로 간주합니다.
    4. 특정 컬럼만 가져올 수 있게 합니다. -> [# 가변 컬럼]
        4-1. pkey와 관련된 특정 정보를 가져오려면 인덱스 지정 필수 -> [# pkey를 이름으로 가져오는 컬럼은 인덱스 지정 필수]
    5. 필터링 및 페이징된 결과를 가져옵니다. -> [# 필터링된 업무 리스트]
    6. 업무 리스트의 정보 중 pkey의 정보를 각 이름으로 변경하고, 검수 중인 문서는 document_id를 제거 후 반환합니다.
        6-1. doc_type_idx로 문서 종류 한글명, 유형 정보를 조회합니다. -> [# doc_type_idx로 문서 종류 이름 검색, 유형(None, 정형, 비정형) 추가]
        6-2. 검수 중이면 document_id 제거 -> [# 검수 중이면 document_id 제거]
        6-3. document_id 제거 -> [# doc_type_index를 이름으로 변경, 문서 유형 추가, document_id 제거]
    """
    return get_document_list_service(
        request = request,
        params = params,
        current_user = current_user,
        session = session
    )


@router.post("/inference")
def get_document_inference_info(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    추론 및 검수 결과
    1. user_email에 따른 권한(정책) 정보를 가져옵니다. -> [# 사용자 권한(정책) 확인]
    2. 문서 정보를 가져옵니다. -> [# 문서 정보 조회]
    3. 해당 문서의 user_team 정보와 사용자의 권한(정책) 정보를 비교 및 문서 열람 제한 -> [# 해당 문서에 대한 권한이 없음]
    4. 요청한 특정 페이지의 추론 및 검수 결과 조회
        2-1. 페이지 수가 1보다 작거나, 해당 문서의 총 페이지 수보다 크면 에러 반환 -> [# 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환]
        2-2. 해당 문서의 특정 페이지에 대한 추론 결과 조회, 없으면 에러 반환 -> [# document_id로 특정 페이지의 가장 최근 inference info 조회]
        2-3. 해당 문서의 특정 페이지에 대한 검수 결과 조회, 가져오기 -> [# 가장 최근 inspect 결과가 있으면 가져오기]
    """
    return get_document_inference_info_service(
        request = request,
        params = params,
        current_user = current_user,
        session = session
    )
