import json

from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set
from fastapi import APIRouter, Depends, Body, Request, Path as fastPath
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.middlewares.exception_handler import CoreCustomException
from app.utils.postprocess import add_unrecognition_kv, add_class_name_kr
from app.utils.image import (
    read_image_from_bytes,
    get_image_bytes,
    image_to_base64,
)
from app.utils.utils import is_admin, get_company_group_prefix

if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



settings = get_settings()
router = APIRouter()


def parse_user_info_list(
    email_user_group_info: Dict[str, schema.UserGroup],
    email_company_user_info: Dict[str, schema.CompanyUserInfo]
) -> List[dict]:
    
    user_info_list: List[dict] = list()
    for user_email, user_group_info in email_user_group_info.items():
        user_info_: dict = dict(
            user_email=user_email,
            user_name=user_group_info.user_info.user_name,
            user_team=user_group_info.user_info.user_team,
            user_team_name=user_group_info.group_info.group_name,
            user_group_name=user_group_info.group_info.group_name,
        )
        
        company_user_info: schema.CompanyUserInfo = email_company_user_info.get(user_email, None)
        if company_user_info is not None:
            user_info_.update(
                company_code   = str(company_user_info.company_info.company_code),
                company_name   = str(company_user_info.company_info.company_name),
                
                user_team_name = str(company_user_info.emp_org_path).split("/")[-1],
                
                user_rgst_t    = str(company_user_info.emp_fst_rgst_dttm),
                user_eno       = str(company_user_info.emp_eno),
                user_nm        = str(company_user_info.emp_usr_nm),
                user_email     = str(company_user_info.emp_usr_emad),
                user_ph        = str(company_user_info.emp_usr_mpno),
                user_tno       = str(company_user_info.emp_inbk_tno),
                
                user_decd      = str(company_user_info.emp_decd),
                user_tecd      = str(company_user_info.emp_tecd),
                user_org_path  = str(company_user_info.emp_org_path),
                user_ofps_cd   = str(company_user_info.emp_ofps_cd),
                user_ofps_nm   = str(company_user_info.emp_ofps_nm)
            )
        
        user_info_list.append(user_info_)
    
    return user_info_list


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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없을 경우 에러 응답 반환
    if group_prefix + select_document_result.user_team not in group_list:
        raise CoreCustomException(2505)
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # page_num 페이지의 가장 최근 추론 결과에서 각도 정보 얻기
    angle = 0
    try:
        select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
        if isinstance(select_inference_result, JSONResponse):
            return select_inference_result
        select_inference_result: schema.InferenceInfo = select_inference_result
        inference_result: dict = select_inference_result.inference_result
        angle = inference_result.get("angle", 0)
    except CoreCustomException:
        angle = 0
    
    # 문서의 page_num 페이지의 썸네일 base64로 encoding
    document_path = Path(str(page_num) + ".png")
    document_bytes = get_image_bytes(document_id, document_path)
    image = read_image_from_bytes(document_bytes, document_path.name, angle, page_num)
    if image is None:
        raise CoreCustomException(2103)
    
    if scale < 0.1: scale = 0.1
    new_w, new_h = ((int(image.size[0] * scale), int(image.size[1] * scale)))
    resized_image = image.resize((new_w, new_h))
    image_base64 = image_to_base64(resized_image)
    
    
    response = dict(
        scale     = scale,
        angle     = -angle,
        width     = new_w,
        height    = new_h,
        thumbnail = image_base64
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/{document_id}/preview")
def get_document_preview(
    document_id:  str,
    scale:        float           = 0.4,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 검수 화면 좌측 문서의 모든 페이지 프리뷰와 문서 종류(소분류) 정보
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_list = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_list, JSONResponse):
        return cls_type_list
    
    doc_type_idx_code: Dict[str, int] = dict()
    for cls_type_info in cls_type_list:
        for doc_type_info in cls_type_info.get("docx_type", {}):
            doc_type_idx_code.update({doc_type_info.get("code"):doc_type_info.get("index")})
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없을 경우 에러 응답 반환
    if group_prefix + select_document_result.user_team not in group_list:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서가 포함한 문서 종류(소분류) 리스트
    doc_type_idxs: dict = select_document_result.doc_type_idxs
    doc_type_total_cnt: Dict[str, int] = dict()
    for doc_type_code in doc_type_idxs.get("doc_type_codes", []):
        doc_type_total_cnt.update({doc_type_code:doc_type_total_cnt.get(doc_type_code, 0) + 1})
    
    # 문서 종류(소분류) 정보
    select_doc_type_all_result = query.select_doc_type_all(session, doc_type_code=list(set(doc_type_idxs.get("doc_type_codes", []))))
    if isinstance(select_doc_type_all_result, JSONResponse):
        return select_doc_type_all_result
    select_doc_type_all_result: List[schema.DocTypeInfo] = select_doc_type_all_result
    
    doc_type_code_info: Dict[str, schema.DocTypeInfo] = dict()
    for doc_type_info in select_doc_type_all_result:
        doc_type_code_info.update({doc_type_info.doc_type_code:doc_type_info})
    
    # 문서의 page_num 페이지의 썸네일 base64로 encoding
    document_path = Path(select_document_result.document_path)
    document_bytes = get_image_bytes(document_id, document_path)
    document_pages: List[Image.Image] = read_image_from_bytes(document_bytes, document_path.name, 0.0, 1, separate=True)
    
    preview_list: List[dict] = list()
    doc_type_code_cnt: Dict[str, int] = dict()
    for page, doc_type_code in zip(range(1, select_document_result.document_pages + 1), doc_type_idxs.get("doc_type_codes", [])):
        doc_type_code_cnt.update({doc_type_code:doc_type_code_cnt.get(doc_type_code, 0) + 1})
        
        doc_type_info = doc_type_code_info.get(doc_type_code)
        doc_type_idx_ = 0
        doc_type_name_ = ""
        
        if doc_type_code not in doc_type_idx_code.keys() or doc_type_info is None:
            doc_type_idx_ = 0
            doc_type_name_ = "기타 서류"
        else:
            doc_type_idx_ = doc_type_info.doc_type_idx
            doc_type_name_ = doc_type_info.doc_type_name_kr
        
        image = document_pages[page-1]
        if image is None:
            status_code, error = ErrorResponse.ErrorCode.get(2103)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        
        if scale < 0.1: scale = 0.1
        new_w, new_h = ((int(image.size[0] * scale), int(image.size[1] * scale)))
        resized_image = image.resize((new_w, new_h))
        image_base64 = image_to_base64(resized_image)
        
        preview_list.append(dict(
            page=page,
            
            page_doc_type=doc_type_code_cnt.get(doc_type_code),
            page_doc_type_total=doc_type_total_cnt.get(doc_type_code),
            
            doc_type_idx=doc_type_idx_,
            doc_type_code=doc_type_info.doc_type_code,
            doc_type_name=doc_type_name_,
            
            scale = scale,
            width= new_w,
            height = new_h,
            thumbnail = image_base64,
            
        ))
    
    
    response = dict(
        preview=preview_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/{doc_type}/kv")
def get_doc_type_kv_list(
    doc_type:     str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 문서 종류(소분류)(doc_type)에서 나올 수 있는 표준 항목코드 정보 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_list = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_list, JSONResponse):
        return cls_type_list
    
    doc_type_idx_code: Dict[str, int] = dict()
    for cls_type_info in cls_type_list:
        for doc_type_info in cls_type_info.get("docx_type", {}):
            doc_type_idx_code.update({doc_type_info.get("code"):doc_type_info.get("index")})
    
    # 요청한 문서 종류가 조회 가능한 문서 목록에 없을 경우 에러 반환
    if doc_type not in doc_type_idx_code.keys():
        status_code, error = ErrorResponse.ErrorCode.get(2509)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    select_doc_type_kv_class_result = query.select_doc_type_kv_class(session, doc_type_idx=doc_type_idx_code.get(doc_type))
    if isinstance(select_doc_type_kv_class_result, JSONResponse):
        return select_doc_type_kv_class_result
    select_doc_type_kv_class_result: List[schema.DocTypeKvClass] = select_doc_type_kv_class_result
    
    kv_list: List[dict] = list()
    for kv_class in select_doc_type_kv_class_result:
        kv_list.append(dict(
            kv_class_code=kv_class.kv_class_info.kv_class_code,
            kv_class_name_kr=kv_class.kv_class_info.kv_class_name_kr,
            kv_class_name_en=kv_class.kv_class_info.kv_class_name_en,
            kv_class_use=str(kv_class.kv_class_info.kv_class_use),
        ))
    
    
    response = dict(
        kv=kv_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/user/inspecter")
def get_filter_user(
    user_team:    str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 업무 리스트 필터링시 조회 가능한 검수자 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 응답 반환
    if group_prefix + user_team not in group_list:
        raise CoreCustomException(2509)
    
    # group_code가 group_prefix + user_team인 그룹에 속한 사용자 목록 조회
    select_user_all_result = query.select_user_group_all(session, group_code=group_prefix + user_team)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserGroup] = select_user_all_result
    
    email_user_info: Dict[str, schema.UserGroup] = dict()
    for user in select_user_all_result:
        email_user_info.update({user.user_email:user})
    
    # (group_code에 속한 사용자가 등록한 문서)를 검수한 사용자 목록 조회
    inspecter_name: Dict[str, schema.UserInfo] = query.get_inspecter_list(session, inspecter_list=[ x.user_email for x in select_user_all_result ])
    if isinstance(inspecter_name, JSONResponse):
        return inspecter_name
    
    email_user_info.update(inspecter_name)
    
    # user_info.user_email이 company_user_info.EMP_USR_EMAD와 같은 유저(=사원) 정보 조회
    select_comapny_user_all_result = query.select_company_user_info_all(session, emp_usr_emad=email_user_info.keys())
    if isinstance(select_comapny_user_all_result, JSONResponse):
        return select_comapny_user_all_result
    select_comapny_user_all_result: List[schema.CompanyUserInfo] = select_comapny_user_all_result
    
    email_company_user_info: Dict[str, schema.CompanyUserInfo] = dict()
    for company_user in select_comapny_user_all_result:
        company_user_info: schema.CompanyUserInfo = company_user
        email_company_user_info.update({company_user_info.emp_usr_emad:company_user_info})
    
    user_info_list = parse_user_info_list(email_user_info, email_company_user_info)
    
    response = dict(
        user_info=user_info_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/user/uploader")
def get_filter_user(
    user_team:    str,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session:      Session         = Depends(db.session)
) -> JSONResponse:
    """
    ### 업무 리스트 필터링시 조회 가능한 등록자 목록 조회
    """
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 응답 반환
    if group_prefix + user_team not in group_list:
        raise CoreCustomException(2509)
    
    # group_code가 group_prefix + user_team인 그룹에 속한 사용자 목록 조회
    select_user_all_result = query.select_user_group_all(session, group_code=group_prefix + user_team)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserGroup] = select_user_all_result
    
    email_user_info: Dict[str, schema.UserGroup] = dict()
    for user in select_user_all_result:
        email_user_info.update({user.user_email:user})
    
    # user_info.user_email이 company_user_info.EMP_USR_EMAD와 같은 유저(=사원) 정보 조회
    select_comapny_user_all_result = query.select_company_user_info_all(session, emp_usr_emad=email_user_info.keys())
    if isinstance(select_comapny_user_all_result, JSONResponse):
        return select_comapny_user_all_result
    select_comapny_user_all_result: List[schema.CompanyUserInfo] = select_comapny_user_all_result
    
    email_company_user_info: Dict[str, schema.CompanyUserInfo] = dict()
    for company_user in select_comapny_user_all_result:
        company_user_info: schema.CompanyUserInfo = company_user
        email_company_user_info.update({company_user_info.emp_usr_emad:company_user_info})
    
    user_info_list = parse_user_info_list(email_user_info, email_company_user_info)
    
    response = dict(
        user_info=user_info_list
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/group")
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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    select_group_all_result = query.select_group_info_all(session, group_code=group_list)
    if isinstance(select_group_all_result, JSONResponse):
        return select_group_all_result
    select_group_all_result: List[schema.GroupInfo] = select_group_all_result
    
    user_team: dict = dict()
    for group in select_group_all_result:
        user_team.update({str(group.group_code).replace(group_prefix, ""):group.group_name})
    
    
    response = dict(
        user_team=user_team
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/filter/cls-type")
def get_filter_cls_type(
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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_list = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_list, JSONResponse):
        return cls_type_list
    
    
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


@router.delete("/list/{document_id}")
async def delete_document_list(
    request: Request,
    document_id: str = fastPath(..., description="문서 아이디"),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
    
) -> JSONResponse:
    """
        업무 리스트 삭제
    """
    
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없을 경우 에러 응답 반환
    if group_prefix + select_document_result.user_team not in group_list:
        raise CoreCustomException(2505)
    
    query.update_document(session, document_id=document_id, is_used=False)
    
    response = {
        "message" : "success"
    }
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
        6-1. cls_type_list로 문서 종류 한글명, 유형 정보를 조회합니다. -> [# cls_type_list 문서 종류 이름 검색, 유형(None, 정형, 비정형) 추가]
        6-2. 검수 중이면 document_id 제거 -> [# 검수 중이면 document_id 제거]
        6-3. document_id 제거 -> [# doc_type_index를 이름으로 변경, 문서 유형 추가, document_id 제거]
    """
    user_email:         str        = current_user.email
    
    # upload_date_start:  str        = params.get("upload_date_start")
    # upload_date_end:    str        = params.get("upload_date_end")
    # inspect_date_start: str        = params.get("inspect_date_start")
    # inspect_date_end:   str        = params.get("inspect_date_end")
    date_sort_desc:     bool       = params.get("date_sort_desc", True)
    upload_date_sort:   bool       = params.get("upload_date_sort", True)
    
    date_start:         str        = params.get("date_start", None)
    date_end:           str        = params.get("date_end", None)
    filter_standard:    str        = params.get("filter_standard", "register")
    
    group_list:         List[str]  = params.get("group_list", [])
    uploader_list:      List[str]  = params.get("uploader_list", [])
    inspecter_list:     List[str]  = params.get("inspecter_list", [])
    doc_type_idx_list:  List[int]  = params.get("doc_type_idx_list", [])
    document_status:    List[str]  = params.get("document_status", [])
    document_filename:  str        = params.get("document_filename", "")
    document_id_list:   List[str]  = params.get("document_id_list", [])
    rows_limit:         int        = params.get("rows_limit", 100)
    rows_offset:        int        = params.get("rows_offset", 0)
    
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_code_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 요청한 그룹이 조회 가능한 그룹 목록에 없을 경우 에러 반환
    for group_code in group_list:
        if group_prefix + group_code not in group_code_list:
            raise CoreCustomException(2509)
    
    # 사용자 정책(조회 가능 문서 대분류 그룹) 확인
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_idx_list_result = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_idx_list_result, JSONResponse):
        return cls_type_idx_list_result
    
    cls_type_idx_result_list: Dict[int, dict] = dict()
    for result in cls_type_idx_list_result:
        cls_type_idx = result.get("index")
        cls_type_idx_result_list.update({cls_type_idx:result})
    
    doc_type_idx_code: Dict[int, dict] = dict()
    for cls_type_info in cls_type_idx_result_list.values():
        for doc_type_info in cls_type_info.get("docx_type", {}):
            doc_type_idx_code.update({doc_type_info.get("index"):doc_type_info})
    
    # 요청한 문서 종류가 조회 가능한 문서 목록에 없을 경우 에러 반환
    for doc_type_idx in doc_type_idx_list:
        if doc_type_idx not in doc_type_idx_code.keys():
            raise CoreCustomException(2509)
    
    # 등록일, 검수일 기간 파싱
    upload_start_date = None
    upload_end_date = None
    inspect_start_date = None
    inspect_end_date = None
    
    upload_date = True if filter_standard == "register" else False
    if upload_date: # 등록일 기준 확인
        try:
            # 기간 요청
            upload_start_date = datetime.strptime(date_start, "%Y.%m.%d")
            upload_end_date = datetime.strptime(date_end, "%Y.%m.%d") + timedelta(days=1)
        except:
            logger.warning(f"날짜의 포맷팅(%Y.%m.%d)이 맞지 않습니다. 기간 없는 전체검색으로 변경합니다.")
            logger.warning(f"date_start: {date_start} date_end: {date_end}")
    else: # filter_standard == "inspector" 검수일 기준 확인
        try:
            # 기간 요청
            inspect_start_date = datetime.strptime(date_start, "%Y.%m.%d")
            inspect_end_date = datetime.strptime(date_end, "%Y.%m.%d") + timedelta(days=1)
        except:
            logger.warning(f"날짜의 포맷팅(%Y.%m.%d)이 맞지 않습니다. 기간 없는 전체검색으로 변경합니다.")
            logger.warning(f"date_start: {date_start} date_end: {date_end}")
    
    # 가변 컬럼
    column_order: list = list()
    cls_index: int = 0
    doc_type_index: int = 0
    docx_id_index: int = 0
    docx_st_index: int = 0
    docx_path_index: int = 0
    uploader_email_index: int = 0
    inspecter_email_index: int = 0
    for i, c in enumerate(settings.DOCUMENT_LIST_COLUMN_ORDER):
        t_c = settings.DCOUMENT_LIST_COLUMN_MAPPING.get(c)
        
        if t_c is None: continue
        
        column_order.append(t_c)
        
        # pkey를 이름으로 가져오는 컬럼은 인덱스 지정 필수
        if t_c == "DocumentInfo.cls_idx":
            cls_index = i
        elif t_c == "DocumentInfo.doc_type_idxs":
            doc_type_index = i
        elif t_c == "DocumentInfo.document_id":
            docx_id_index = i
        elif t_c == "InspectInfo.inspect_status":
            docx_st_index = i
        elif t_c == "DocumentInfo.document_path":
            docx_path_index = i
        elif t_c == "DocumentInfo.user_email":
            uploader_email_index = i
        elif t_c == "InspectInfo.user_email":
            inspecter_email_index = i
    
    # 필터링된 업무 리스트
    total_count, complet_count, filtered_count, filtered_rows = query.select_document_inspect_all(
        session,
        upload_start_date=upload_start_date,
        upload_end_date=upload_end_date,
        
        inspect_start_date=inspect_start_date,
        inspect_end_date=inspect_end_date,
        
        upload_date=upload_date,
        
        date_sort_desc=date_sort_desc,
        upload_date_sort=upload_date_sort,
        
        user_team=user_team_list,
        uploader_list=uploader_list,
        inspecter_list=inspecter_list,
        
        doc_type_idx_list=doc_type_idx_list,
        
        document_status=document_status,
        document_filename=document_filename,
        document_id_list=document_id_list,
        
        rows_limit=rows_limit,
        rows_offset=rows_offset,
        column_order=column_order
    )
    if isinstance(filtered_rows, JSONResponse):
        return filtered_rows
    
    # 등록자, 검수자 user_info 조회
    email_list: List[str] = list()
    email_list.extend( [ row[uploader_email_index] for row in filtered_rows ] )
    email_list.extend( [ row[inspecter_email_index] for row in filtered_rows ] )
    
    # group_code가 group_prefix + user_team인 그룹에 속한 사용자 목록 조회
    select_user_all_result = query.select_user_group_all_multi(session, user_email=email_list)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserGroup] = select_user_all_result
    
    email_user_info: Dict[str, schema.UserGroup] = dict()
    for user in select_user_all_result:
        email_user_info.update({user.user_email:user})
    
    # user_info.user_email이 company_user_info.EMP_USR_EMAD와 같은 유저(=사원) 정보 조회
    select_comapny_user_all_result = query.select_company_user_info_all(session, emp_usr_emad=email_user_info.keys())
    if isinstance(select_comapny_user_all_result, JSONResponse):
        return select_comapny_user_all_result
    select_comapny_user_all_result: List[schema.CompanyUserInfo] = select_comapny_user_all_result
    
    email_company_user_info: Dict[str, schema.CompanyUserInfo] = dict()
    for company_user in select_comapny_user_all_result:
        company_user_info: schema.CompanyUserInfo = company_user
        email_company_user_info.update({company_user_info.emp_usr_emad:company_user_info})
    
    user_info_list = parse_user_info_list(email_user_info, email_company_user_info)
    
    user_email_name: Dict[str, str] = dict()
    for user_info in user_info_list:
        user_email_name.update({user_info.get("user_email"):user_info.get("user_team_name")})
    
    # cls_idx를 이름으로 변경, 문서 유형 추가, document_id 제거
    # rows: List[list] = filtered_rows
    response_rows: List[list] = list()
    for row in filtered_rows:
        
        # doc_type_idxs: dict = json.loads(row.pop(doc_type_index).replace("'", "\""))
        doc_type_idxs: dict = row.pop(doc_type_index)
        doc_type_idx_first = doc_type_idxs.get("doc_type_idxs", [0])[0]
        
        doc_type_cnt = 0
        doc_type_etc = 0
        for doc_type in set(doc_type_idxs.get("doc_type_idxs", [])):
            if doc_type in doc_type_idx_code.keys(): doc_type_cnt += 1
            else: doc_type_etc = 1
        
        row.insert(doc_type_index, doc_type_cnt + doc_type_etc - 1)
        
        # cls_idx -> doc_type_name_kr
        if cls_index != 0:
            cls_idx = row.pop(cls_index)
            row.insert(cls_index, doc_type_idx_code.get(doc_type_idx_first, {}).get("name_kr"))
        
        # 검수 상태 매핑
        if docx_st_index > 0:
            docx_status = row.pop(docx_st_index)
            row.insert(docx_st_index, settings.STATUS_MAPPING.get(docx_status, ""))
        
        # document_path -> 문서명
        if docx_path_index > 0:
            document_path = row.pop(docx_path_index)
            row.insert(docx_path_index, document_path.split("/")[-1])
        
        # user_email로 팀(그룹)명 찾기
        if uploader_email_index > 0:
            row.pop(uploader_email_index + 2)
            row.insert(uploader_email_index + 2, user_email_name.get(row[uploader_email_index], "None"))
        
        if uploader_email_index > 0:
            row.pop(inspecter_email_index + 2)
            row.insert(inspecter_email_index + 2, user_email_name.get(row[inspecter_email_index], "None"))
        
        # 문자열로 변환
        response_rows.append( [ str(x) for x in row ] )
    
    
    response = dict(
        total_count=total_count,
        complet_count=complet_count,
        filtered_count=filtered_count,
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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 해당 문서에 대한 권한이 없음
    if group_prefix + select_document_result.user_team not in group_list:
        raise CoreCustomException(2505)
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 오류 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # 검수 중인데 자신의 검수 중인 문서가 아니거나 관리자가 아닐 경우 에러 응답 반환
    inspect_id = select_document_result.inspect_id
    select_inspect_result = query.select_inspect_latest(session, inspect_id=inspect_id)
    if isinstance(select_inspect_result, JSONResponse):
        return select_inspect_result
    select_inspect_result: schema.InspectInfo = select_inspect_result
    if select_inspect_result.inspect_status == settings.STATUS_INSPECTING:
        if not is_admin(user_policy_result) and select_inspect_result.user_email != user_email:
            raise CoreCustomException(2511)
    
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
    
    if select_inference_result.inference_result.get("kv", None):
        # 인식 되지 않은 class None값으로 추가
        select_inference_result, _ = add_unrecognition_kv(session, select_inference_result)
        # kv에 kv_class_name_kr 한글명 추가
        select_inference_result = add_class_name_kr(session, select_inference_result)
    
    
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
