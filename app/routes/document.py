import requests  # type: ignore

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from app.utils.utils import cal_time_elapsed_seconds
from app.schemas import error_models as ErrorResponse
from app.utils.document import (
    get_page_count,
    is_support_format,
    save_upload_document,
)
from app.utils.image import (
    get_crop_image,
    get_image_info_from_bytes,
    get_image_bytes,
    load_image,
)



settings = get_settings()
router = APIRouter()



@router.post("/list")
def get_document_list(
    request: dict = Body(...), session: Session = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링 및 페이징
    1. user_email에 따른 팀과 권한(그룹, 역할) 정보를 가져옵니다.
        1-1. 사용자 정보 조회 -> [# 자신의 사용자 정보 조회, # 조직 정보]
        1-2. 가장 최근에 인가된 권한 정보 조회 -> [# 자신의 권한(그룹, 역할) 정보 조회]
        1-3. 조회 가능한 부서를 권한 정보에 따라 업무 리스트 조회 제한 -> [# 슈퍼어드민(0) 또는 관리자(1)이 아닐경우 자신의 조직으로 업무 리스트 조회 제한]
    2. 요청한 필터링 항목을 db에 조회가능한 데이터로 변환합니다.
        2-1. 문서 등록자의 아이디 정보 조회 -> [# 유저 이름으로 업로더 아이디(이메일) 검색]
        2-2. 문서 검수자의 아이디 정보 조회 -> [# 유저 이름으로 검수자 아이디(이메일) 검색]
        2-3. 검수 기간 파싱 -> [# 검수일 기간 파싱]
            2-3-1. 검수 기간 파싱 실패를 전체 검수일 기간으로 간주합니다.
    3. 특정 컬럼만 가져올 수 있게 합니다. -> [# 가변 컬럼]
        3-1. pkey와 관련된 특정 정보를 가져오려면 인덱스 지정 필수 -> [# pkey를 이름으로 가져오는 컬럼은 인덱스 지정 필수]
    4. 필터링 및 페이징된 결과를 가져옵니다. -> [# 필터링된 업무 목록]
    5. 업무 리스트의 정보 중, 아이디(이메일)과 조직ID정보를 각각 유저 이름과 조직명으로 변경합니다
        5-1. db에 조회가능한 데이터로 변환 -> [# 업무 리스트에 존재하는 아이디(이메일), 조직ID로 중복없는 리스트 만들기]
            5-1-1. 문서 등록자, 검수자 이름 정보 조회 -> [# 아이디(이메일)로 유저 이름 검색]
            5-1-2. 조직명 정보 조회 -> [# 조직ID로 조직명 검색]
        5-2. 아이디(이메일)과 유저 이름, 조직ID와 조직명을 맵핑 -> [# 조직ID를 조직명으로, 아이디(이메일)을 이름으로 변경]
    """
    user_email = request.get("user_email", "do@not.use")
    inspect_date_start = request.get("inspect_date_start")
    inspect_date_end = request.get("inspect_date_end")
    department = request.get("department", [])
    uploader_name = request.get("uploader_name", [])
    inspecter_name = request.get("inspecter_name", [])
    document_type = request.get("document_type", [])
    document_model_type = request.get("document_model_type", [])
    saved = request.get("saved", [])
    inspect_status = request.get("inspect_status", [])
    rows_limit = request.get("rows_limit", 100)
    rows_offset = request.get("rows_offset", 0)
    
    # 자신의 사용자 정보 조회
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    
    # 조직 정보
    user_team: str = select_user_result.user_team
    del select_user_result
    
    # 자신의 권한(그룹, 역할) 정보 조회
    select_user_role_result = query.select_user_role_latest(session, user_email=user_email)
    if isinstance(select_user_role_result, JSONResponse):
        return select_user_role_result
    
    # 슈퍼어드민(0) 또는 관리자(1)이 아닐경우 자신의 조직으로 업무 리스트 조회 제한
    user_role_index = select_user_role_result.role_index
    if user_role_index not in [0, 1]:
        department = list([user_team])
    if isinstance(department, str):
        department = list([department])
    del select_user_role_result
    
    # 유저 이름으로 업로더 아이디(이메일) 검색
    select_uploader_result = query.select_user_all(
        session,
        user_name=uploader_name,
        user_team=department
    )
    if isinstance(select_uploader_result, JSONResponse):
        return select_uploader_result
    uploader_list = list()
    for result in select_uploader_result:
        uploader_list.append(result.user_email)
    del select_uploader_result
    
    # 유저 이름으로 검수자 아이디(이메일) 검색
    select_inspecter_result = query.select_user_all(
        session,
        user_name=inspecter_name,
        user_team=department
    )
    if isinstance(select_inspecter_result, JSONResponse):
        return select_inspecter_result
    inspecter_list = list()
    for result in select_inspecter_result:
        inspecter_list.append(result.user_email)
    del select_inspecter_result
    
    # 검수일 기간 파싱
    ignore_date: bool
    start_date = datetime(2022, 6, 1, 0, 0, 0, 0)
    end_date = datetime.now()
    try:
        # 기간 요청
        start_date = datetime.strptime(inspect_date_start, "%Y.%m.%d")
        end_date = datetime.strptime(inspect_date_end, "%Y.%m.%d")
        ignore_date = False
    except:
        # 전체 기간 요청
        start_date = datetime(2022, 6, 1, 0, 0, 0, 0)
        end_date = datetime.now()
        ignore_date = True
    
    # 가변 컬럼
    column_order: list = list()
    email_u_index: int = 0
    email_i_index: int = 0
    team_index: int = 0
    for i, c in enumerate(settings.DOCUMENT_LIST_COLUMN_ORDER):
        t_c = settings.DCOUMENT_LIST_COLUMN_MAPPING.get(c)
        column_order.append(t_c)
        
        # pkey를 이름으로 가져오는 컬럼은 인덱스 지정 필수
        if t_c == "DocumentInfo.user_team":
            team_index = i
        elif t_c == "DocumentInfo.user_email":
            email_u_index = i
        elif t_c == "InspectInfo.user_email":
            email_i_index = i
    
    # 필터링된 업무 리스트
    total_count, complet_count, filtered_rows = query.select_document_inspect_all(
        session,
        ignore_date=ignore_date,
        start_date=start_date,
        end_date=end_date,
        user_team=department,
        uploader_list=uploader_list,
        inspecter_list=inspecter_list,
        document_type=document_type,
        document_model_type=document_model_type,
        inspect_status=inspect_status,
        rows_limit=rows_limit,
        rows_offset=rows_offset,
        column_order=column_order
    )
    
    # 업무 리스트에 존재하는 아이디(이메일), 조직ID로 중복없는 리스트 만들기
    user_email_set: set = set()
    user_team_set: set = set()
    for filtered_row in filtered_rows:
        user_team_set.add(filtered_row[team_index])
        user_email_set.add(filtered_row[email_u_index])
        user_email_set.add(filtered_row[email_i_index])
    
    user_email_list = list(user_email_set)
    user_team_list = list(user_team_set)
    
    # 아이디(이메일)로 유저 이름 검색
    user_email_name: dict = dict()
    select_user_all_result = query.select_user_all(session, user_email=user_email_list)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    for result in select_user_all_result:
        user_email_name.update(dict({result.user_email:result.user_name}))
    del select_user_all_result, user_email_list, user_email_set
    
    # 조직ID로 조직명 검색
    user_team_name: dict = dict()
    select_team_all_result = query.select_org_all(session, org_org_id=user_team_list)
    if isinstance(select_team_all_result, JSONResponse):
        return select_team_all_result
    for result in select_team_all_result:
        user_team_name.update(dict({result.org_org_id:result.org_org_nm}))
    del select_team_all_result, user_team_list, user_team_set
    
    # 조직ID를 조직명으로, 아이디(이메일)을 이름으로 변경
    for filtered_row in filtered_rows:
        filtered_row[team_index] = user_team_name.get(filtered_row[team_index], None)
        filtered_row[email_u_index] = user_email_name.get(filtered_row[email_u_index], None)
        filtered_row[email_i_index] = user_email_name.get(filtered_row[email_i_index], None)
    
    
    response = dict({
        "total_count": total_count,
        "complet_count": complet_count,
        "columns": settings.DOCUMENT_LIST_COLUMN_ORDER,
        "rows":filtered_rows
    })
    
    return JSONResponse(content=jsonable_encoder(response))


@router.post("/inference")
def get_document_inference_info(
    request: dict = Body(...), session: Session = Depends(db.session)
) -> JSONResponse:
    """
    추론 및 검수 결과
    1. user_email에 따른 팀과 권한(그룹, 역할) 정보를 가져옵니다.
        1-1. 사용자 정보 조회 -> [# 자신의 사용자 정보 조회, # 조직 정보]
        1-2. 가장 최근에 인가된 권한 정보 조회 -> [# 자신의 권한(그룹, 역할) 정보 조회]
        1-3. 조회 가능한 부서를 권한 정보에 따라 추론 및 검수 결과 조회 제한 -> [# 슈퍼어드민(0) 또는 관리자(1)이 아닐경우 추론 또는 검수 결과 조회 제한]
        1-4. 조회 가능한 추론 및 검수 결과가 아닐 경우 오류 반환 -> [# 슈퍼어드민 또는 관리자가 아닌데 다른 부서의 문서를 보려고 한다면 오류 반환]
    2. 요청한 특정 페이지의 추론 및 검수 결과 조회
        2-1. 페이지 수가 1보다 작거나, 해당 문서의 총 페이지 수보다 크면 에러 반환 -> [# 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환]
        2-2. 해당 문서의 특정 페이지에 대한 추론 결과 조회, 없으면 에러 반환 -> [# document_id로 특정 페이지의 가장 최근 inference info 조회]
        2-3. 해당 문서의 특정 페이지에 대한 검수 결과 조회, 가져오기 -> [# 가장 최근 inspect 결과가 있으면 가져오기]
    """
    user_email = request.get("user_email", "do@not.use")
    document_id = request.get("document_id", "")
    page_num = request.get("page_num", 0)
    
    # 자신의 사용자 정보 조회
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    
    # 조직 정보
    user_team: str = select_user_result.user_team
    del select_user_result
    
    # 자신의 권한(그룹, 역할) 정보 조회
    select_user_role_result = query.select_user_role_latest(session, user_email=user_email)
    if isinstance(select_user_role_result, JSONResponse):
        return select_user_role_result
    
    # 슈퍼어드민(0) 또는 관리자(1)이 아닐경우 추론 및 검수 결과 조회 제한
    is_admin = True if select_user_role_result.role_index in [0 , 1] else False
    del select_user_role_result
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    
    # 슈퍼어드민 또는 관리자가 아닌데 다른 부서의 문서를 보려고 한다면 오류 반환
    if is_admin is False and select_document_result.user_team != user_team:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # document_id로 특정 페이지의 가장 최근 inference info 조회
    select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
    if isinstance(select_inference_result, JSONResponse):
        return select_inference_result
    select_inference_result: schema.InferenceInfo = select_inference_result
    inference_id = select_inference_result.inference_id
    
    # 가장 최근 inspect 결과가 있으면 가져오기
    select_inspect_result = query.select_inspect_latest(session, inference_id=inference_id)
    if isinstance(select_inspect_result, JSONResponse):
        return select_inspect_result
    
    
    response = dict({
        "document_id":select_inference_result.document_id,
        "user_email":select_inference_result.user_email,
        "user_team":select_inference_result.user_team,
        "inference_result":select_inference_result.inference_result,
        "inference_type":select_inference_result.inference_type,
        "model_index":select_inference_result.model_index,
        
        "inspect_result": select_inspect_result.inspect_result if select_inspect_result else None,
        
        "page_doc_type":select_inference_result.page_doc_type,
        "page_width":select_inference_result.page_width,
        "page_height":select_inference_result.page_height
    })
    
    return JSONResponse(content=jsonable_encoder(response))