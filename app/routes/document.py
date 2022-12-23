from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set
from fastapi import APIRouter, Depends, Body, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import hydra_cfg
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.utils.image import (
    read_image_from_bytes,
    get_image_bytes,
    image_to_base64,
)
from app.utils.utils import is_admin

if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



settings = get_settings()
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
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없을 경우 에러 응답 반환
    if select_document_result.user_team not in user_team_list:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서의 page_num 페이지의 썸네일 base64로 encoding
    document_path = Path(select_document_result.document_path)
    document_bytes = get_image_bytes(document_id, document_path)
    image = read_image_from_bytes(document_bytes, document_path.name, 0.0, page_num)
    if image is None:
        status_code, error = ErrorResponse.ErrorCode.get(2103)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    if scale < 0.1: scale = 0.1
    new_w, new_h = ((int(image.size[0] * scale), int(image.size[1] * scale)))
    resized_image = image.resize((new_w, new_h))
    image_base64 = image_to_base64(resized_image)
    
    
    response = dict(
        scale     = scale,
        width     = new_w,
        height    = new_h,
        thumbnail = image_base64
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/user")
def get_filter_user(
    user_team:    str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 업무 리스트 필터링시 조회 가능한 등록자, 검수자 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 응답 반환
    if user_team not in user_team_list:
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # user_team에 속한 사용자 목록 조회
    select_user_all_result = query.select_user_all(session, user_team=user_team_list)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserInfo] = select_user_all_result
    
    email_name: Dict[str, str] = dict()
    for user in select_user_all_result:
        email_name.update({user.user_email:user.user_name})
    
    # (user_team에 속한 사용자가 등록한 문서)를 검수한 사용자 목록 조회
    inspecter_name: Dict[str, str] = query.get_inspecter_list(session, user_team_list=user_team_list)
    if isinstance(inspecter_name, JSONResponse):
        return inspecter_name
    
    email_name.update(inspecter_name)
    
    
    response = dict(
        user_info=email_name
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/department")
def get_filter_department(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 조회 가능한 부서(=그룹.그룹코드) = user_team(=group_info.group_code) 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    select_group_all_result = query.select_group_info_all(session, group_code=user_team_list)
    if isinstance(select_group_all_result, JSONResponse):
        return select_group_all_result
    select_group_all_result: List[schema.GroupInfo] = select_group_all_result
    
    user_team: dict = dict()
    for group in select_group_all_result:
        user_team.update({group.group_code:group.group_name})
    
    
    response = dict(
        user_team=user_team
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/cls-type")
def get_filter_doc_type(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 사용가능한 문서 종류(대분류) 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    cls_type_list = query.get_user_classification_type(session, user_policy_result)
    
    
    response = dict(
        cls_type=cls_type_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/docx-type")
def get_filter_doc_type(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    업무 리스트 필터링시 사용가능한 문서 종류(소분류) 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    docx_type_list = query.get_user_document_type(session, user_policy_result)
    
    
    response = dict(
        docx_type=docx_type_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


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
    user_email:         str        = current_user.email
    upload_date_start:  str        = params.get("upload_date_start")
    upload_date_end:    str        = params.get("upload_date_end")
    inspect_date_start: str        = params.get("inspect_date_start")
    inspect_date_end:   str        = params.get("inspect_date_end")
    date_sort_desc:     bool       = params.get("date_sort_desc", True)
    group_list:         List[str]  = params.get("group_list", [])
    uploader_list:      List[str]  = params.get("uploader_list", [])
    inspecter_list:     List[str]  = params.get("inspecter_list", [])
    doc_type_idx_list:  List[int]  = params.get("doc_type_idx_list", [])
    doc_structed:       List[str]  = params.get("doc_structed", [])
    document_status:    List[str]  = params.get("document_status", [])
    rows_limit:         int        = params.get("rows_limit", 100)
    rows_offset:        int        = params.get("rows_offset", 0)
    
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    
    # 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 반환
    for group_code in group_list:
        if group_code not in user_team_list:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 사용자 정책(조회 가능 문서 종류) 확인
    doc_type_list: List[str] = list()
    doc_type_list.extend(user_policy_result.get("R_DOC_TYPE_CATEGORY", []))
    doc_type_list.extend(user_policy_result.get("R_DOC_TYPE_SUB_CATEGORY", []))
    doc_type_list = list(set(doc_type_list))
    
    select_doc_type_all_result = query.select_doc_type_all(session, doc_type_code=doc_type_list)
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    select_doc_type_all_result: List[schema.DocTypeInfo] = select_doc_type_all_result
    
    doc_type_idx_result_list: List[int] = list()
    for result in select_doc_type_all_result:
        doc_type_idx_result_list.append(result.doc_type_idx)
    
    # 요청한 문서 종류가 조회 가능한 문서 목록에 없을 경우 에러 반환
    for doc_type_idx in doc_type_idx_list:
        if doc_type_idx not in doc_type_idx_result_list:
            status_code, error = ErrorResponse.ErrorCode.get(2509)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서 유형 필터 없었으면 "None" 추가
    if len(doc_structed) == 0:
        doc_structed.extend(["None", "정형", "비정형", "반정형"])
    
    # 등록일, 검수일 기간 파싱
    ignore_upload_date: bool = True
    upload_start_date = None
    upload_end_date = None
    ignore_inpsect_date: bool = True
    inspect_start_date = None
    inspect_end_date = None
    try:
        # 기간 요청
        ignore_upload_date = False
        upload_start_date = datetime.strptime(upload_date_start, "%Y.%m.%d")
        upload_end_date = datetime.strptime(upload_date_end, "%Y.%m.%d") + timedelta(days=1)
    except:
        # 전체 기간 요청
        ignore_upload_date = True
        upload_start_date = datetime(2022, 6, 1, 0, 0, 0, 0)
        upload_end_date = datetime.now() + timedelta(days=1)
    
    try:
        # 기간 요청
        ignore_inpsect_date = False
        inspect_start_date = datetime.strptime(inspect_date_start, "%Y.%m.%d")
        inspect_end_date = datetime.strptime(inspect_date_end, "%Y.%m.%d") + timedelta(days=1)
    except:
        # 전체 기간 요청
        ignore_inpsect_date = True
        inspect_start_date = datetime(2022, 6, 1, 0, 0, 0, 0)
        inspect_end_date = datetime.now() + timedelta(days=1)
    
    # 가변 컬럼
    column_order: list = list()
    doc_type_index: int = 0
    for i, c in enumerate(settings.DOCUMENT_LIST_COLUMN_ORDER):
        t_c = settings.DCOUMENT_LIST_COLUMN_MAPPING.get(c)
        if t_c is not None: column_order.append(t_c)
        
        # pkey를 이름으로 가져오는 컬럼은 인덱스 지정 필수
        if t_c == "DocumentInfo.doc_type_idx":
            doc_type_index = i
    
    # 필터링된 업무 리스트
    total_count, complet_count, filtered_rows = query.select_document_inspect_all(
        session,
        ignore_upload_date=ignore_upload_date,
        upload_start_date=upload_start_date,
        upload_end_date=upload_end_date,
        
        ignore_inpsect_date=ignore_inpsect_date,
        inspect_start_date=inspect_start_date,
        inspect_end_date=inspect_end_date,
        
        date_sort_desc=date_sort_desc,
        
        user_team=user_team_list,
        uploader_list=uploader_list,
        inspecter_list=inspecter_list,
        
        doc_type_idx_list=doc_type_idx_list,
        
        document_status=document_status,
        rows_limit=rows_limit,
        rows_offset=rows_offset,
        column_order=column_order
    )
    if isinstance(filtered_rows, JSONResponse):
        return filtered_rows
    
    # 업무 리스트에 존재하는 doc_type_idx로 중복없는 리스트로 변경
    doc_type_idx_list: set = set()
    for filtered_row in filtered_rows:
        doc_type_idx_list.add(filtered_row[doc_type_index])
    doc_type_idx_list = list(set(doc_type_idx_list))
    
    # doc_type_idx로 문서 종류 이름 검색, 유형(정형, 비정형, 반정형) 추가
    doc_type_idx_name: Dict[str, str] = dict()
    doc_type_idx_structed: Dict[str, bool] = dict()
    select_doc_type_all_result = query.select_doc_type_all(session, doc_type_idx=doc_type_idx_list)
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    for result in select_doc_type_all_result:
        doc_type_idx_name.update(dict({str(result.doc_type_idx):result.doc_type_name_kr}))
        doc_type_idx_structed.update(dict({str(result.doc_type_idx):result.doc_type_structed}))
    del select_doc_type_all_result, doc_type_idx_list
    
    # 검수 중이면 document_id 제거
    docx_id_index = 0
    insp_st_index = 8
    try:
        docx_id_index = settings.DOCUMENT_LIST_COLUMN_ORDER.index("document_id")
        insp_st_index = settings.DOCUMENT_LIST_COLUMN_ORDER.index("상태")
    except:
        docx_id_index = 0
        insp_st_index = 8
    
    # doc_type_index를 이름으로 변경, 문서 유형 추가, document_id 제거
    rows: List[list] = filtered_rows
    response_rows: List[list] = list()
    for row in rows:
        
        structed = doc_type_idx_structed.get(row[doc_type_index])
        
        if structed not in doc_structed: continue
        
        row[doc_type_index] = doc_type_idx_name.get(row[doc_type_index], "None")
        row.insert(doc_type_index + 1, structed)
        
        if row[insp_st_index] in [settings.STATUS_RUNNING_INFERENCE, settings.STATUS_INSPECTING] \
            and not is_admin(user_policy_result):
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
    user_email:  str = current_user.email
    document_id: str = params.get("document_id")
    page_num:    int = params.get("page_num", 0)
    
    # 사용자 권한(정책) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list.extend(user_policy_result.get("R_INFERENCE_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없음
    if select_document_result.user_team not in user_team_list:
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

