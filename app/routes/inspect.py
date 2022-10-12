import copy
from datetime import datetime
from typing import List
from app.services.inspect import get_diff_array_item_indexes, get_inspect_accuracy, get_item_list_in_index, get_flatten_table_content

from fastapi import APIRouter, Depends, Body, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.database.connection import db
from app.database import query, schema
from app.common.const import get_settings
from app.utils.logging import logger
from app.utils.utils import get_ts_uuid, is_admin
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel

if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user



settings = get_settings()
router = APIRouter()

@router.post("/save")
def kbl_post_inspect_info(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    '''
    교보생명 고객사 검수 데이터 저장

    교보생명은 개인정보 이슈로 inference 데이터를 직접 저장할 수 없습니다. 그래서 매번 inference 결과를 받아서 inspect와 비교하고,
    거기서 달라진 것을 기반으로 정확도를 산출합니다. 그리고 최종 검수 결과는 kv의 경우 항목코드만 남기고 tables의 경우 인덱스만 남깁니다.


    '''
    user_email:         str   = current_user.email
    document_id:        str   = params.get("document_id")
    page_num:           int   = params.get("page_num", 1)
    inspect_date_start: str   = params.get("inspect_date_start")
    inspect_date_end:   str   = params.get("inspect_date_end")
    inspect_doc_type:    str   = params.get("inspect_doc_type")
    inference_result:   dict  = params.get("inference_result", {})
    inspect_result:     dict  = params.get("inspect_result", {})
    inspect_done:       bool  = params.get("inspect_done", False)

    # 사용자 정보 조회
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result

    # 사용자 권한 조회
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list = list(set(user_team_list))

    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 문서 상태가 RUNNING_INFERENCE면 에러 응답 반환
    # if select_document_result.inspect_id == "RUNNING_INFERENCE":
    #     status_code, error = ErrorResponse.ErrorCode.get(2513)
    #     return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서에 대한 권한이 없을 경우 에러 응답 반환
    if select_document_result.user_team not in user_team_list:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 검수 중인데 자신의 검수 중인 문서가 아니거나 관리자가 아닐 경우 에러 응답 반환
    inspect_id = select_document_result.inspect_id
    select_inspect_result = query.select_inspect_latest(session, inspect_id=inspect_id)
    if isinstance(select_inspect_result, JSONResponse):
        return select_inspect_result
    select_inspect_result: schema.InspectInfo = select_inspect_result
    if select_inspect_result.inspect_status == settings.STATUS_INSPECTING:
        if not is_admin(user_policy_result) and select_inspect_result.user_email != user_email:
            status_code, error = ErrorResponse.ErrorCode.get(2511)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 검수 결과 저장 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # doc_type 검수 비교
    doc_type = copy.deepcopy(query.select_doc_type_code(session, document_id=document_id))
    if doc_type != inspect_doc_type:
        doc_type_idxs = []
        doc_type_codes = []
        doc_type_codes.append(inspect_doc_type)
        doc_type_idxs.append(query.select_doc_type(session, doc_type_code=inspect_doc_type).doc_type_idx)

        # doc_type 검수 내용 반영
        inspected_document = query.update_document(
            session, 
            document_id=document_id, 
            doc_type_idxs=doc_type_idxs, 
            doc_type_codes=doc_type_codes)
    
    # 검수 kv 비교
    inference_texts = list(map(lambda x:x.get("value"), inference_result["prediction"]["key_values"]))
    inspect_texts = list(map(lambda x:x.get("value"), inspect_result["prediction"]["key_values"]))
    changed_text_indexs = get_diff_array_item_indexes(inference_texts, inspect_texts)
    # 검수 후 변경된 항목 코드 리스트
    inspect_doc_type_codes = get_item_list_in_index((list(map(lambda x:x.get("key"), inspect_result["prediction"]["key_values"]))), changed_text_indexs)

    # 검수 tables 비교  
    inference_tables = inference_result["prediction"]["tables"]
    inspect_tables = inspect_result["prediction"]["tables"]

    # 다차원 배열을 하나의 array로 만들어야함
    inference_table_contents = get_flatten_table_content(inference_tables)
    inspect_table_contents = get_flatten_table_content(inspect_tables)
    changed_table_indexs = get_diff_array_item_indexes(inference_table_contents, inspect_table_contents)
    inspect_table_codes = get_item_list_in_index(inspect_table_contents, changed_table_indexs)

    # 검수 정확도 측정 - kv개수 + table 개수
    inspect_accuracy = get_inspect_accuracy(inspect_texts, inspect_table_contents, inspect_doc_type_codes, inspect_table_codes)

    inspect_date_end = inspect_date_end if inspect_date_end else datetime.now()

    # 검수 결과 저장 - inspect_result = kv는 항목코드, tables는 수정된 값의 인덱스 
    insert_inspect_result = query.insert_inspect(
        session,
        inspect_id = get_ts_uuid("inpsect"),
        user_email = current_user.email,
        user_team = current_user.team,
        inference_id = query.select_inference_latest(session, document_id=document_id, page_num=page_num).inference_id,
        inspect_start_time = inspect_date_start,
        inspect_end_time = inspect_date_end if inspect_done else None,
        inspect_result = jsonable_encoder({"kv" : inspect_doc_type_codes, "el" : changed_table_indexs}),
        inspect_accuracy = inspect_accuracy,
        inspect_status = settings.STATUS_INSPECTED if inspect_done else settings.STATUS_INSPECTING
    )

    if isinstance(insert_inspect_result, JSONResponse):
        return insert_inspect_result
    del insert_inspect_result

    # 가장 최근 검수 정보 업데이트
    update_document_result = query.update_document(
        session,
        document_id,
        inspect_id=inspect_id
    )
    if isinstance(update_document_result, JSONResponse):
        return update_document_result
    del update_document_result
    
    
    response = dict(
        resource_id=dict(
            inspect_id=inspect_id
        )
    )
    
    return JSONResponse(status_code=201, content=jsonable_encoder(response))





@router.post("/save/old")
def post_inspect_info(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    검수 정보 임시 저장 및 저장
    TODO 에러응답 추가
        inspect_date_startㅣ 없을때
        inspect_done True인데 inpsect_end_time이 없을때
    """
    user_email:         str   = current_user.email
    document_id:        str   = params.get("document_id")
    page_num:           int   = params.get("page_num", 0)
    inspect_date_start: str   = params.get("inspect_date_start")
    inspect_date_end:   str   = params.get("inspect_date_end")
    inspect_result:     dict  = params.get("inspect_result", {})
    inspect_accuracy:   float = params.get("inspect_accuracy", 0.0)
    inspect_done:       bool  = params.get("inspect_done", False)
    
    # 사용자 정보 조회
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 문서 상태가 RUNNING_INFERENCE면 에러 응답 반환
    if select_document_result.inspect_id == "RUNNING_INFERENCE":
        status_code, error = ErrorResponse.ErrorCode.get(2513)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 문서에 대한 권한이 없을 경우 에러 응답 반환
    if select_document_result.user_team not in user_team_list:
        status_code, error = ErrorResponse.ErrorCode.get(2505)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 검수 중인데 자신의 검수 중인 문서가 아니거나 관리자가 아닐 경우 에러 응답 반환
    inspect_id = select_document_result.inspect_id
    select_inspect_result = query.select_inspect_latest(session, inspect_id=inspect_id)
    if isinstance(select_inspect_result, JSONResponse):
        return select_inspect_result
    select_inspect_result: schema.InspectInfo = select_inspect_result
    if select_inspect_result.inspect_status == settings.STATUS_INSPECTING:
        if not is_admin(user_policy_result) and select_inspect_result.user_email != user_email:
            status_code, error = ErrorResponse.ErrorCode.get(2511)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # 검수 결과 저장 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        status_code, error = ErrorResponse.ErrorCode.get(2506)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    # document_id로 특정 페이지의 가장 최근 inference info.inference_id 조회
    select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
    if isinstance(select_inference_result, JSONResponse):
        return select_inference_result
    select_inference_result: schema.InferenceInfo = select_inference_result
    inference_id = select_inference_result.inference_id
    
    # inference_id에 해당하는 추론에 대한 검수 결과 저장
    inspect_id = get_ts_uuid("inpsect")
    inspect_status = settings.STATUS_INSPECTING
    if inspect_done is True:
        inspect_status = settings.STATUS_INSPECTED
        inspect_date_end = inspect_date_end if inspect_date_end else datetime.now()
    else:
        inspect_date_end = None
    insert_inspect_result = query.insert_inspect(
        session,
        inspect_id=inspect_id,
        user_email=user_email,
        user_team=select_user_result.user_team,
        inference_id=inference_id,
        inspect_start_time=inspect_date_start,
        inspect_end_time=inspect_date_end,
        inspect_result=inspect_result,
        inspect_accuracy=inspect_accuracy,
        inspect_status=inspect_status
    )
    if isinstance(insert_inspect_result, JSONResponse):
        return insert_inspect_result
    del insert_inspect_result
    
    # 가장 최근 검수 정보 업데이트
    update_document_result = query.update_document(
        session,
        document_id,
        inspect_id=inspect_id
    )
    if isinstance(update_document_result, JSONResponse):
        return update_document_result
    del update_document_result
    
    
    response = dict(
        resource_id=dict(
            inspect_id=inspect_id
        )
    )
    
    return JSONResponse(status_code=201, content=jsonable_encoder(response))
