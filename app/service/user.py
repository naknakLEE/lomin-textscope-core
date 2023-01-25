from datetime import datetime, timedelta
from typing import List, Dict, Union
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import urllib.parse

from app.models import UserInfo as UserInfoInModel
from app.middlewares.exception_handler import CoreCustomException
from app.utils.logging import logger

from app.common.const import get_settings
from app.database import query, schema
from app.utils.utils import is_admin, get_ts_uuid, get_company_group_prefix

settings = get_settings()

def get_user_info_by_user_email(
    user_email:   str,
    session:      Session,
    current_user: UserInfoInModel,
) -> JSONResponse:
    
    user_email = urllib.parse.unquote(user_email)
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_user_info, JSONResponse):
        raise CoreCustomException(2509)
    request_user_info: schema.CompanyUserInfo = request_user_info
    request_company_info: schema.CompanyInfo = request_user_info.company_info
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 자신이 아닌 다른 사원의 정보를 조회하는데 관리자가 아닐경우 에러 응답 반환
    if user_email != current_user.email and not is_admin(user_policy_result):
        raise CoreCustomException(2509)
    
    # user_email이 가지고 있는 모든 정책(권한) 정보 조회
    target_user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(target_user_policy_result, JSONResponse):
        return target_user_policy_result
    target_user_policy_result: dict = target_user_policy_result
    
    # emp_usr_emad=user_email인 사원의 정보
    company_user_info = query.select_company_user_info(session, emp_usr_emad=user_email)
    if isinstance(company_user_info, JSONResponse):
        return company_user_info
    company_user_info: schema.CompanyUserInfo = company_user_info
    company_info: schema.CompanyInfo = company_user_info.company_info
    
    # 해당 사원의 회사가 current_user.email의 회사와 다르면 에러 응답 반환
    if company_info.company_code != request_company_info.company_code:
        raise CoreCustomException(2509)
    
    # 권한 확인 및 개인 권한 적용 기간 조회
    authority = query.get_user_authority(target_user_policy_result)
    authority_time = query.get_user_policy_time(session, user_email, authority)
    
    response = dict(
        user_info = dict(
            company_code  = str(company_info.company_code),
            company_name  = str(company_info.company_name),
            
            user_rgst_t   = str(company_user_info.emp_fst_rgst_dttm),
            user_eno      = str(company_user_info.emp_eno),
            user_nm       = str(company_user_info.emp_usr_nm),
            user_email    = str(company_user_info.emp_usr_emad),
            user_ph       = str(company_user_info.emp_usr_mpno),
            user_tno      = str(company_user_info.emp_inbk_tno),
            
            user_decd     = str(company_user_info.emp_decd),
            user_tecd     = str(company_user_info.emp_tecd),
            user_org_path = str(company_user_info.emp_org_path),
            user_ofps_cd  = str(company_user_info.emp_ofps_cd),
            user_ofps_nm  = str(company_user_info.emp_ofps_nm),
            authority     = str(authority),
            authority_time_start = str(authority_time.get("start_time"))[:10],
            authority_time_end   = str(authority_time.get("end_time"))[:10]
        )
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

def post_user_policy(
    user_email:str,
    authority: str,
    authority_time_start: str,
    authority_time_end:   str,
    session:      Session,
    current_user: UserInfoInModel,
) -> JSONResponse:
    
    user_email = urllib.parse.unquote(user_email)
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_company_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_company_user_info, JSONResponse):
        raise CoreCustomException(2509)
    request_company_user_info: schema.CompanyUserInfo = request_company_user_info
    request_company_info: schema.CompanyInfo = request_company_user_info.company_info
    request_user_info: schema.UserInfo = request_company_user_info.user_info
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 자신이 아닌 다른 사원의 정보를 조회하는데 관리자가 아닐경우 에러 응답 반환
    if user_email != current_user.email and not is_admin(user_policy_result):
        raise CoreCustomException(2509)
    
    # emp_usr_emad=user_email인 사원의 정보
    target_company_user_info = query.select_company_user_info(session, emp_usr_emad=user_email)
    if isinstance(target_company_user_info, JSONResponse):
        return target_company_user_info
    target_company_user_info: schema.CompanyUserInfo = target_company_user_info
    target_company_info: schema.CompanyInfo = target_company_user_info.company_info
    target_user_info: schema.UserInfo = target_company_user_info.user_info
    
    # 해당 사원의 회사가 current_user.email의 회사와 다르면 에러 응답 반환
    if target_company_info.company_code != request_company_info.company_code:
        raise CoreCustomException(2509)
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, user_email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    try:
        authority_time_start = datetime.strptime(authority_time_start, "%Y.%m.%d")
        authority_time_end = datetime.strptime(authority_time_end, "%Y.%m.%d")
        
        if authority_time_end - authority_time_start > timedelta(days=365):
            authority_time_end = authority_time_start + timedelta(days=365)
    except:
        logger.warning(f"날짜의 포맷팅(%Y.%m.%d)이 맞지 않습니다. 권한 적용 기간을 1 개월로 변경합니다.")
        authority_time_start = datetime.now().date()
        authority_time_end = datetime.now().date() + timedelta(days=30)
    
    group_code_src = group_prefix
    if authority.find("관리자") != -1:
        group_code_src += "admin"
    elif authority.find("일반") != -1:
        group_code_src += target_user_info.user_team
    elif authority.find("없음") != -1:
        group_code_src += "normal"
    else:
        group_code_src += ""
    
    select_group_policy_result: List[schema.GroupPolicy] = query.select_group_policy(session, group_code_src)
    for group_policy in select_group_policy_result:
        query.upsert_user_group_policy(
            session,
            user_email,
            group_policy.policy_code,
            group_policy.policy_content,
            authority_time_start,
            authority_time_end
        )
    
    if group_code_src.find("admin") == -1:
        for admin_code in settings.ADMIN_POLICY:
            query.delete_user_group_policy(session, user_email, admin_code)
    
    inputs = dict(
        user_email=user_email,
        authority=authority,
        authority_src=group_code_src,
        authority_time_start=authority_time_start,
        authority_time_end=authority_time_end
    )
    
    insert_log_result = query.insert_log(
        session=session,
        log_id=get_ts_uuid("log"),
        log_type=group_prefix + "AUTHORITY",
        user_email=current_user.email,
        user_team=request_user_info.user_team,
        log_content=dict({"request": inputs})
    )
    
    
    response = dict(
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

def get_all_policy_log(
    authority_date_start: str,
    authority_date_end:   str,
    session:      Session,
    current_user: UserInfoInModel,
) -> JSONResponse:
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 관리자가 아닐경우 에러 응답 반환
    if is_admin(user_policy_result) is False:
        raise CoreCustomException(2509)
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    try:
        authority_date_start = datetime.strptime(authority_date_start, "%Y.%m.%d")
        authority_date_end = datetime.strptime(authority_date_end, "%Y.%m.%d")
        
        if authority_date_end - authority_date_start > timedelta(days=365):
            authority_date_end = authority_date_start + timedelta(days=365)
    except:
        logger.warning(f"날짜의 포맷팅(%Y.%m.%d)이 맞지 않습니다. 로그 조회 기간을 1 개월로 변경합니다.")
        authority_date_start = datetime.now().date()
        authority_date_end = datetime.now().date() + timedelta(days=30)
    
    select_log_result = query.get_log_all_by_created_time(
        session,
        authority_date_start,
        authority_date_end,
        log_type=group_prefix + "AUTHORITY"
    )
    
    # 아이디(이메일) 정보를 
    user_email_list = [ x.user_email for x in select_log_result ]
    user_email_list.extend( [ x.log_content.get("request", {}).get("user_email") for x in select_log_result ] )
    user_email_list = list(set(user_email_list))
    
    select_user_all_result = query.select_user_all(session, user_email=user_email_list)
    if isinstance(select_user_all_result, JSONResponse):
        return select_user_all_result
    select_user_all_result: List[schema.UserInfo] = select_user_all_result
    
    email_user_info: Dict[str, schema.UserInfo] = { user.user_email:user for user in select_user_all_result }
    
    log_authority = [ (
        str(x.created_time),
        str(x.user_email),
        str(email_user_info.get(x.user_email, schema.UserInfo()).user_name),
        str(x.log_content.get("request", {}).get("user_email", "None")),
        str(email_user_info.get(x.log_content.get("request", {}).get("user_email", ""), schema.UserInfo()).user_name),
        str(x.log_content.get("request", {}).get("authority")),
        str(x.log_content.get("request", {}).get("authority_time_start")),
        str(x.log_content.get("request", {}).get("authority_time_end"))
    ) for x in select_log_result ]
    
    
    response = dict(
        total_count=len(select_log_result),
        columns=["권한 설정 시각", "관리자", "관리자 이름", "구성원", "구성원 이름", "권한", "권한 적용 시작", "권한 적용 종료"],
        rows=log_authority
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))    

def get_company_users_authority(
    search_text:  str,
    rows_limit:   int,
    rows_offset:  int,
    filter_authority: str,
    session:      Session,
    current_user: UserInfoInModel,
) -> JSONResponse:
    
    # emp_usr_emad=current_user.email인 사원의 정보
    request_user_info = query.select_company_user_info(session, emp_usr_emad=current_user.email)
    if isinstance(request_user_info, JSONResponse):
        raise CoreCustomException(2509)
    request_user_info: schema.CompanyUserInfo = request_user_info
    # request_company_info: schema.CompanyInfo = request_user_info.company_info
    
    # current_user.email이 가지고 있는 모든 정책(권한) 정보 조회
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 관리자가 아닐경우 에러 응답 반환
    if is_admin(user_policy_result) is False:
        raise CoreCustomException(2509)
    
    # 검색어 수 제한
    search_text = search_text[:50]
    filter_authority = filter_authority[:10]
    
    # current_user와 같은 company에 속한 company_user 정보를 조회
    total_count, select_company_user_query = query.select_company_user_info_query(session, search_text, company_code=request_user_info.company_code)
    select_company_user_query: List[schema.CompanyUserInfo] = select_company_user_query
    
    company_user_info_dict: Dict[str, schema.CompanyUserInfo] = { x.emp_usr_emad : x for x in select_company_user_query }
    
    filtered_count = 0
    response_rows: List[list] = list()
    company_user_info_list: Dict[str, Dict[str, Union[bool, list]]] = query.get_user_group_policy_all(session, user_email_list=company_user_info_dict.keys())
    for company_user_email, company_user_policy in company_user_info_list.items():
        # 권한 확인
        authority = query.get_user_authority(company_user_policy)
        
        if authority in filter_authority:
            filtered_count += 1
            
            if rows_offset > 0: 
                rows_offset -= 1
                continue
            
            if len(response_rows) < rows_limit:
                company_user_info = company_user_info_dict.get(company_user_email)
                
                # 개인 권한 적용 기간 조회
                authority_time = query.get_user_policy_time(session, company_user_email, authority)
                
                response_rows.append([
                    str(company_user_info.emp_eno),
                    str(company_user_info.emp_usr_nm),
                    str(company_user_info.emp_ofps_nm),
                    str(authority),
                    str(company_user_info.emp_usr_emad),
                    str(company_user_info.emp_inbk_tno),
                    str(company_user_info.emp_org_path),
                    str(company_user_info.emp_fst_rgst_dttm)[:10],
                    str(authority_time.get("start_time"))[:10],
                    str(authority_time.get("end_time"))[:10],
                ])
    
    
    response = dict(
        total_count=total_count,
        filtered_count=filtered_count,
        columns=["행번", "이름", "직위", "권한", "이메일", "내선번호", "부서", "사원 등록일", "권한 적용 시작 시각", "권한 적용 종료 시각"],
        rows=response_rows
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))