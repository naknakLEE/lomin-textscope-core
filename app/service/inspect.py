import copy
from datetime import datetime
from typing import List, Dict
from app.services.inspect import get_inspect_accuracy, get_flatten_table_content, get_removed_changes_keyvalue

from app.utils.document import generate_searchable_pdf_2, get_stored_file_extension
from fastapi import Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import hydra_cfg
from app.database import query, schema
from app.common.const import get_settings
from app.utils.utils import get_ts_uuid, is_admin, get_company_group_prefix
from app.utils.image import get_image_bytes, read_image_from_bytes
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from pathlib import Path
from app.middlewares.exception_handler import CoreCustomException

if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


settings = get_settings()


def kbl_post_inspect_info(
    request: Request,
    params: dict,
    current_user: UserInfoInModel,
    session: Session
) -> JSONResponse:
    '''
    교보생명 고객사 검수 데이터 저장

    교보생명은 개인정보 이슈로 inference 데이터를 직접 저장할 수 없습니다. 그래서 매번 inference 결과를 받아서 inspect와 비교하고,
    거기서 달라진 것을 기반으로 정확도를 산출합니다. 그리고 최종 검수 결과는 kv의 경우 항목코드만 남기고 tables의 경우 인덱스만 남깁니다.


    '''
    user_email:         str   = current_user.email
    document_id:        str   = params.get("document_id")
    page_num:               int   = params.get("page", 1)
    changes_keyvalue:   list   = params.get("changes_keyvalue")
    changes_doctype:    dict   = params.get("changes_doctype")
    
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
    if len(changes_doctype) > 0:
        if changes_doctype["prediction"] != "" and changes_doctype["corrected"] != "":
            try:
                doc_type = copy.deepcopy(query.select_doc_type_code(session, document_id=document_id))
            except:
                status_code, error = ErrorResponse.ErrorCode.get(2524)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        if doc_type != changes_doctype['corrected']:
            doc_type_idxs = []
            doc_type_codes = []
            doc_type_codes.append(changes_doctype['corrected'])
            doc_type_idxs.append(query.select_doc_type(session, doc_type_code=changes_doctype['corrected']).doc_type_idx)

            # doc_type 검수 내용 반영
            inspected_document = query.update_document(
                session, 
                document_id=document_id, 
                doc_type_idxs=doc_type_idxs, 
                doc_type_codes=doc_type_codes)
    
    if len(changes_keyvalue) > 0:
        # inference 데이터 불러오기
        latest_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
        if isinstance(latest_inference_result, JSONResponse):
            return latest_inference_result
        # inference 전체 kv 중 score가 0이 아닌 실제 인식된 kv 
        inspected_kv = list(filter(lambda x: latest_inference_result.inference_result['kv'][x].get("score") > 0, latest_inference_result.inference_result['kv']))
        # 수정 - (인식된 kv 개수 + 미인식 kv 중 수정된 개수) = kv개수 
        uninspected_kv = list(filter(lambda x: x.get("key") not in inspected_kv, changes_keyvalue))
        total_kv = inspected_kv + uninspected_kv

        

        # inference 전체 table cell 개수
        inference_tables = []
        if 'tables' in latest_inference_result.inference_result.keys():
            inference_tables = get_flatten_table_content(latest_inference_result.inference_result['tables'])
        
        # 검수 정확도 측정 - kv개수 + table 개수
        inspect_accuracy = get_inspect_accuracy(
                kv_list=total_kv,
                el_list=inference_tables,
                kv_changed=changes_keyvalue,
                el_changed=[]
        )
                
        inspect_date_start = datetime.now()
        inspect_date_end = datetime.now()

        # 개인정보 제거
        removed_changes_keyvalue = get_removed_changes_keyvalue(changes_keyvalue)

        # 검수 결과 저장 - inspect_result = kv는 항목코드, tables는 수정된 값의 인덱스 
        insert_inspect_result = query.insert_inspect(
            session,
            inspect_id = get_ts_uuid("inpsect"),
            user_email = current_user.email,
            user_team = current_user.team,
            inference_id = latest_inference_result.inference_id,
            inspect_start_time = inspect_date_start,
            inspect_end_time = inspect_date_end, 
            inspect_result = jsonable_encoder({"changed_keyvalue" : removed_changes_keyvalue}),
            inspect_accuracy = inspect_accuracy,
            inspect_status = settings.STATUS_INSPECTED 
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
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))


def post_inspect_info(
    request: Request,
    params: dict,
    background_tasks: BackgroundTasks,
    current_user: UserInfoInModel,
    session: Session
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
    # inspect_date_start: str   = params.get("inspect_date_start", datetime.now())
    # inspect_date_end:   str   = params.get("inspect_date_end")
    inspect_result:     dict  = params.get("inspect_result")
    # inspect_accuracy:   float = params.get("inspect_accuracy", 0.0)
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
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_INSPECT_TEAM", []))
    user_team_list = list(set(user_team_list))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 사용자 정책(조회 가능 문서 종류(대분류)) 확인
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_idx_list_result = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_idx_list_result, JSONResponse):
        return cls_type_idx_list_result
    
    cls_type_idx_result_list: Dict[int, dict] = { x.get("index") : x for x in cls_type_idx_list_result }
    cls_type_doc_type_list: Dict[int, List[int]] = { cls_type : [ x.get("index") for x in doc_type.get("docx_type", []) ] for cls_type, doc_type in cls_type_idx_result_list.items() }
    
    # 사용자 정책(조회 가능 문서 종류(소분류)) 확인
    doc_type_idx_code: Dict[int, dict] = dict()
    for cls_type_info in cls_type_idx_result_list.values():
        for doc_type_info in cls_type_info.get("docx_type", []):
            doc_type_idx_code.update({doc_type_info.get("index"):doc_type_info})
    
    # 문서 상태가 RUNNING_INFERENCE면 에러 응답 반환
    # if select_document_result.inspect_id == "RUNNING_INFERENCE":
    #     raise CoreCustomException(2513)
    
    # 문서에 대한 권한이 없을 경우 에러 응답 반환
    if select_document_result.user_team not in user_team_list:
        raise CoreCustomException(2505)
    
    # 검수 중인데 자신의 검수 중인 문서가 아니거나 관리자가 아닐 경우 에러 응답 반환
    inspect_id = select_document_result.inspect_id
    if inspect_id != 'RUNNING_INFERENCE':
        select_inspect_result = query.select_inspect_latest(session, inspect_id=inspect_id)
        if isinstance(select_inspect_result, JSONResponse):
            return select_inspect_result
        select_inspect_result: schema.InspectInfo = select_inspect_result
        if select_inspect_result.inspect_status == settings.STATUS_INSPECTING:
            if not is_admin(user_policy_result) and select_inspect_result.user_email != user_email:
                raise CoreCustomException(2511)
    
    # 검수 결과 저장 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # document_id로 특정 페이지의 가장 최근 inference info.inference_id 조회
    select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
    if isinstance(select_inference_result, JSONResponse):
        return select_inference_result
    select_inference_result: schema.InferenceInfo = select_inference_result
    inference_id = select_inference_result.inference_id
    
    # inference_id에 해당하는 추론에 대한 검수 결과 저장
    inspect_id = get_ts_uuid("inpsect")
    inspect_end_time = None
    inspect_status = settings.STATUS_INSPECTING
    if inspect_done is True: 
        inspect_status = settings.STATUS_INSPECTED
        inspect_end_time = datetime.now()

    insert_inspect_result = query.insert_inspect(
        session,
        auto_commit=True,
        inspect_id=inspect_id,
        user_email=user_email,
        user_team=select_user_result.user_team,
        inference_id=inference_id,
        inspect_result=inspect_result,
        inspect_status=inspect_status,
        inspect_end_time=inspect_end_time
    )

    if isinstance(insert_inspect_result, JSONResponse):
        return insert_inspect_result
    del insert_inspect_result

    if inspect_done is True and select_document_result.document_pages == page_num:
        background_tasks.add_task(
            generate_put_pdf,
            select_document_result,
            inspect_result,
            document_id,
            session                    
        )
    # 가장 최근 검수 정보, 문서 평균 정확도 업데이트
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
    
    return JSONResponse(status_code=201, content=jsonable_encoder(response), background=background_tasks)


def generate_put_pdf(
    select_document_result:schema.DocumentInfo,
    inspect_result: dict,
    document_id: str,
    session: Session,
):
    """
        수정 pdf 생성하기(background용으로 따로 빼놈)
    """
    angle_images = list()
    document_extension = get_stored_file_extension(select_document_result.document_path)
    angle = inspect_result.get("angle", 0)
    for page in range(1, select_document_result.document_pages + 1):
        document_page_path = Path(str(page) + document_extension)
        document_regist_date:str = str(select_document_result.document_path)[:10]
        real_docx_id = "/".join([document_regist_date, document_id])                
        document_bytes = get_image_bytes(real_docx_id, document_page_path)
        angle_image = read_image_from_bytes(document_bytes, document_page_path.name, angle, page)
        if angle_image is None:
            raise CoreCustomException(2103)
        angle_images.append(angle_image)
    
    # document_id에 해당하는 inference_result 리스트 생성
    select_document_inference_result_list = query.select_inference_all(session, document_id=document_id)
    select_document_inference_result_list: List[schema.InferenceInfo] = select_document_inference_result_list
    document_inference_results = list(map(lambda x : x.inference_result, select_document_inference_result_list))

    
    for idx, result in enumerate(document_inference_results):
        # inspect가 있는 경우 적용
        latest_inspect_result = query.select_inspect_latest(
                session, inference_id=select_document_inference_result_list[idx].inference_id)
        if latest_inspect_result is not None:
            document_inference_results[idx] = latest_inspect_result.inspect_result
        # image 적용
        # document_inference_results[idx]['base64_encode_file'] = base64_images[idx]
    
    # pdf 생성
    pdf_input = {
        'inspect_result_list' : document_inference_results,
        'pdf_file_name' : select_document_result.document_path,
        'pil_image_list' : angle_images
    }
    generate_searchable_pdf_2(pdf_input)