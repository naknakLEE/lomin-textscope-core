import requests  # type: ignore

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from app.utils.utils import cal_time_elapsed_seconds
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
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
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



settings = get_settings()
router = APIRouter()



@router.get("/filter/user")
def get_filter_user(
    dept_id: str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    ### 업무 리스트 필터링시 조회 가능한 등록자, 검수자 목록 조회
    """
    user_email: str = current_user.email
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 슈퍼어드민 또는 관리자 여부 조회
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
    # 슈퍼어드민 또는 관리자이 아닐경우 자신의 조직으로 업무 리스트 필터 항목 제한
    if not is_admin and user_team != dept_id:
        status_code, error = ErrorResponse.ErrorCode.get(2510)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # dept_id에 속한 모든 사용자 목록 조회
    select_user_all_result = query.select_user_all(session, user_team=[dept_id])
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserInfo] = select_user_all_result
    
    email_name: dict = dict()
    for user in select_user_all_result:
        email_name.update(dict({
            user.user_email: user.user_name
        }))
    
    
    response = dict({
        "users": email_name
    })
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/department")
def get_filter_department(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 조회 가능한 부서 목록 조회
    """
    user_email: str = current_user.email
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 슈퍼어드민 또는 관리자 여부 조회
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
    # 슈퍼어드민 또는 관리자이 아닐경우 자신의 조직으로 업무 리스트 필터 항목 제한
    inputs = dict()
    if not is_admin: inputs.update(dict(org_org_id=[user_team]))
    
    # 부서레벨이 "부서"(org_dept_lvl_val=3)인 부서 목록 조회
    select_org_all_result: List[schema.KeiOrgInfo] = list()
    select_org_all_result = query.select_org_all(session, org_dept_lvl_val=["3"], **inputs)
    if isinstance(select_org_all_result, JSONResponse):
        return select_org_all_result
    select_org_all_result: List[schema.KeiOrgInfo] = select_org_all_result
    
    org_id_name: dict = dict()
    for org in select_org_all_result:
        org_id_name.update(dict({
            org.org_org_id: org.org_org_nm
        }))
    
    response = dict({
        "departments": org_id_name
    })
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/docx-type")
def get_filter_doc_type(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 사용가능한 문서 종류 목록 조회
    """
    user_email: str = current_user.email
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 슈퍼어드민 또는 관리자 여부 조회
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
    # 슈퍼어드민 또는 관리자이 아닐경우 자신의 조직으로 업무 리스트 필터 항목 제한
    inputs = dict()
    if not is_admin: inputs.update(dict(org_org_id=[user_team]))
    
    # TODO 사용가능한 문서 종류 정책 확인 추가 필요
    select_doc_type_all_result = query.select_doc_type_all(session)
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    
    docx_type_list = list()
    for result in select_doc_type_all_result:
        docx_type_list.append({
            "index": result.doc_type_idx,
            "code": result.doc_type_code if result.doc_type_code else "None",
            "name_kr": result.doc_type_name_kr,
            "name_en": result.doc_type_name_en,
        })
    
    
    response = {
        "docx_type": docx_type_list
    }
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.post("/list")
def get_document_list(
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링 및 페이징
    1. user_email에 따른 팀과 권한(그룹, 역할) 정보를 가져옵니다.
        1-1. 사용자 정보 조회 -> [# 자신의 사용자 정보 조회, # 조직 정보]
        1-2. 사용자가 슈퍼어드민 또는 관리자인지 조회 -> [# 슈퍼어드민 또는 관리자 여부 조회]
        1-3. 조회 가능한 문서 종류를 권한 정보에 따라 업무 리스트 조회 제한 -> [# TODO 사용가능한 문서 종류 정책 확인 추가 필요]
        1-4. 조회 가능한 부서를 권한 정보에 따라 업무 리스트 조회 제한 -> [# 슈퍼어드민 또는 관리자이 아닐경우 자신의 조직으로 업무 리스트 조회 제한]
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
        5-2. 검수 중이면 document_id 제거 -> [# 검수 중이면 document_id 제거]
        5-3. 각 key들을 이름으로 변경, document_id 제거 -> [# 조직ID를 조직명으로, 아이디(이메일)을 이름으로, doc_type_index를 이름으로 변경, 문서 유형 추가, document_id 제거]
    """
    user_email:         List[str]  = params.get("user_email", current_user.email)
    inspect_date_start: str        = params.get("inspect_date_start")
    inspect_date_end:   str        = params.get("inspect_date_end")
    department:         List[str]  = params.get("dept_name", [])
    uploader_name:      List[str]  = params.get("uploader_name", [])
    inspecter_name:     List[str]  = params.get("inspecter_name", [])
    doc_type_idx:       List[int]  = params.get("doc_type_idx", [])
    doc_structed:       List[str]  = params.get("doc_structed", [])
    saved:              List[bool] = params.get("saved", [])
    inspect_status:     List[str]  = params.get("inspect_status", [])
    rows_limit:         int        = params.get("rows_limit", 100)
    rows_offset:        int        = params.get("rows_offset", 0)
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 슈퍼어드민 또는 관리자 여부 조회
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
    # 슈퍼어드민 또는 관리자이 아닐경우 자신의 조직으로 업무 리스트 조회 제한
    if not is_admin:
        department = list([user_team])
    if isinstance(department, str):
        department = list([department])
    
    # TODO 사용가능한 문서 종류 정책 확인 추가 필요
    doc_type_idx_list = doc_type_idx
    
    # 문서 유형 필터 없었으면 "None" 추가
    if len(doc_structed) == 0:
        doc_structed.append("None")
    
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
    doc_type_index: int = 0
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
        elif t_c == "DocumentInfo.doc_type_idx":
            doc_type_index = i
    
    # 필터링된 업무 리스트
    total_count, complet_count, filtered_rows = query.select_document_inspect_all(
        session,
        ignore_date=ignore_date,
        start_date=start_date,
        end_date=end_date,
        user_team=department,
        uploader_list=uploader_list,
        inspecter_list=inspecter_list,
        doc_type_idx_list=doc_type_idx_list,
        inspect_status=inspect_status,
        rows_limit=rows_limit,
        rows_offset=rows_offset,
        column_order=column_order
    )
    if isinstance(filtered_rows, JSONResponse):
        return filtered_rows
    
    # 업무 리스트에 존재하는 아이디(이메일), 조직ID로 중복없는 리스트 만들기
    user_email_set: set = set()
    user_team_set: set = set()
    doc_type_idx_set: set = set()
    for filtered_row in filtered_rows:
        user_team_set.add(filtered_row[team_index])
        user_email_set.add(filtered_row[email_u_index])
        user_email_set.add(filtered_row[email_i_index])
        doc_type_idx_set.add(filtered_row[doc_type_index])
    
    user_email_list = list(user_email_set)
    user_team_list = list(user_team_set)
    doc_type_idx_list = list(doc_type_idx_set)
    
    # doc_type_idx로 문서 종류 이름 검색, 유형(정형, 비정형) 추가
    doc_type_idx_name: Dict[str, str] = dict()
    doc_type_idx_structed: Dict[str, bool] = dict()
    select_doc_type_all_result = query.select_doc_type_all(session, doc_type_idx=doc_type_idx_list)
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    for result in select_doc_type_all_result:
        doc_type_idx_name.update(dict({str(result.doc_type_idx):result.doc_type_name_kr}))
        doc_type_idx_structed.update(dict({str(result.doc_type_idx):result.doc_type_structed}))
    del select_doc_type_all_result, doc_type_idx_list, doc_type_idx_set
    
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
    
    # 검수 중이면 document_id 제거
    docx_id_index = 0
    insp_st_index = 8
    try:
        docx_id_index = settings.DOCUMENT_LIST_COLUMN_ORDER.index("Docx ID")
        insp_st_index = settings.DOCUMENT_LIST_COLUMN_ORDER.index("검수 상태")
    except:
        docx_id_index = 0
        insp_st_index = 8
    
    # 조직ID를 조직명으로, 아이디(이메일)을 이름으로, doc_type_index를 이름으로 변경, 문서 유형 추가, document_id 제거
    rows: List[list] = filtered_rows
    response_rows: List[list] = list()
    for row in rows:
        
        structed = doc_type_idx_structed.get(row[doc_type_index])
        if structed == True: structed = "정형"
        elif structed == False: structed = "비정형"
        else: structed = "None"
        
        if structed not in doc_structed: continue
        
        row[team_index] = user_team_name.get(row[team_index], "None")
        row[email_u_index] = user_email_name.get(row[email_u_index], "None")
        row[email_i_index] = user_email_name.get(row[email_i_index], "None")
        row[doc_type_index] = doc_type_idx_name.get(row[doc_type_index], "None")
        row.insert(doc_type_index + 1, structed)
        
        if row[insp_st_index] is settings.INSPECT_STATUS_SUSPEND:
            row[docx_id_index] = ""
        
        response_rows.append(row)
    
    
    response = dict(
        total_count=total_count,
        complet_count=complet_count,
        columns=settings.DOCUMENT_LIST_COLUMN_ORDER,
        rows=response_rows
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.post("/inference")
def get_document_inference_info(
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    추론 및 검수 결과
    1. user_email에 따른 팀과 권한(그룹, 역할) 정보를 가져옵니다.
        1-1. 사용자 정보 조회 -> [# 자신의 사용자 정보 조회, # 조직 정보]
        1-2. 사용자가 슈퍼어드민 또는 관리자인지 조회 -> [# 슈퍼어드민 또는 관리자 여부 조회]
        1-3. 조회 가능한 추론 및 검수 결과가 아닐 경우 오류 반환 -> [# 슈퍼어드민 또는 관리자가 아닌데 다른 부서의 문서를 보려고 한다면 오류 반환]
    2. 요청한 특정 페이지의 추론 및 검수 결과 조회
        2-1. 페이지 수가 1보다 작거나, 해당 문서의 총 페이지 수보다 크면 에러 반환 -> [# 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환]
        2-2. 해당 문서의 특정 페이지에 대한 추론 결과 조회, 없으면 에러 반환 -> [# document_id로 특정 페이지의 가장 최근 inference info 조회]
        2-3. 해당 문서의 특정 페이지에 대한 검수 결과 조회, 가져오기 -> [# 가장 최근 inspect 결과가 있으면 가져오기]
    """
    user_email: str  = params.get("user_email", current_user.email)
    document_id: str = params.get("document_id")
    page_num: int    = params.get("page_num", 0)
    
    # 자신의 사용자 정보 조회
    # 조직 정보
    # 슈퍼어드민 또는 관리자 여부 조회
    team_role = query.get_user_team_role(session, user_email=user_email)
    if isinstance(team_role, JSONResponse):
        return team_role
    user_team, is_admin = team_role
    
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
    select_inspect_result: schema.InspectInfo = select_inspect_result
    
    
    response = dict(
        document_id=select_inference_result.document_id,
        user_email=select_inference_result.user_email,
        user_team=select_inference_result.user_team,
        inference_result=select_inference_result.inference_result,
        inference_type=select_inference_result.inference_type,
        
        inspect_result=select_inspect_result.inspect_result if select_inspect_result else None,
        
        doc_type_idx=select_inference_result.doc_type_idx,
        page_width=select_inference_result.page_width,
        page_height=select_inference_result.page_height
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))