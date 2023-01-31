from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import OAuth2PasswordRequestForm, UserInfo as UserInfoInModel
from fastapi import APIRouter, Body, Depends, Request

from fastapi.encoders import jsonable_encoder
from app import hydra_cfg
from app.common.const import get_settings
from app.utils.auth import create_access_token
from app.utils.logging import logger
from app.service import docx
from app.routes.inference import ocr



from app.utils.document import (
    delete_document,
    document_path_verify,
    get_page_count,
    is_support_format,
    save_upload_document,
)
from app.schemas import error_models as ErrorResponse
from app.utils.minio import MinioService
from app.utils.utils import cal_time_elapsed_seconds, get_ts_uuid
from app.database.connection import db 
from app.database import query, schema
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user
"""
    ### Base Function API
    불필요한 파라미터 및 작업들을 다 걷어낸 순수한 기능만을 담은 API<br/>
    DataBase 연동 X<br/>
    TASK_ID(ClickUp): CU-2unzy4h
"""

settings = get_settings()   # default setting
router = APIRouter()
minio_client = MinioService()   # minio service setting

@router.post("/auth")
async def post_auth_token(
    inputs: OAuth2PasswordRequestForm = Depends()
) -> JSONResponse:
    """
    ### [Base]전용 OAuth2.0 토큰 발급
    입력받은 Email을 토대로 OAuth2.0 토큰을 생성후 Return
    """
    # AceessToken 만료시간 세팅
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # OAuth2.0 생성 
    access_token = create_access_token(
        data={"sub": inputs.email, "scopes": inputs.scopes},
        expires_delta=access_token_expires,
    )
    
    # Return response
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder({
            "access_token": access_token,
            "token_type": "Bearer"
        })
    )

@router.post("/docx")
async def post_upload_document(
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [Base]전용 문서 업로드
    base64encoding된 문서 data와 문서 파일명을 토대로 적재(minio or local)후 DB에 Document Info Insert<br>
    문서 고유 ID(document_id) return
    """
    # 시작 시간 측정
    request_datetime = datetime.now()

    user_email:str    = current_user.email
    document_name:str = inputs.get("document_name")
    document_data:str = inputs.get("document_data")

    response: dict = dict(resource_id=dict())
    response_log: dict = dict()
    request_datetime = datetime.now()
    
    # 업로드된 파일 포맷(확장자) 확인
    is_support = is_support_format(document_name)
    # 지원하지 않은 포맷(확장자)일시 "지원하지 않는 파일 형식입니다" Error return
    if is_support is False:
        status_code, error = ErrorResponse.ErrorCode.get(2105)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # 유저 정보 확인(Document Info Insert시 유저 정보가 필요하여서 실행함..)
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team        

    # 고유한 document_id 생성 -> DB적재용이 아닌 path를 만들기 위함!
    document_id = get_ts_uuid("document")

    # 문서 저장(minio or local pc)
    save_success, save_path = save_upload_document(document_id, document_name, document_data)

    # 문서 저장에 실패하였을 경우 "문서 정보를 저장하는 중 에러가 발생했습니다" Error return
    if not save_success:
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # 문서 저장에 성공했을시, document 테이블에 insert        
    document_pages, document_name = get_page_count(document_data, document_name)
    logger.info(f"success save document document_id : {document_id}")
    # 기존 document insert에서 document_description, doc_type_idx, document_type 제외
    dao_document_params = {
        "document_id": document_id,
        "user_email": user_email,
        "user_team": user_team,
        "document_path": save_path,
        "document_pages": document_pages,
    }
    insert_document_result = query.insert_document(session, **dao_document_params)
    if isinstance(insert_document_result, JSONResponse):
        return insert_document_result            

    # 종료 시간 측정 
    response_datetime = datetime.now()
    # 걸린 시간 측정 (종료시간 - 시작시간)
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    # response log 생성(시작시간, 종료시간, 걸린시간)
    response_log.update(
        dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        )
    )
    
    # response 객체 생성
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
        document_id = document_id,
    )

    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.post("/docx/delete")
async def post_delete_document(
    inputs: Dict = Body(...),
) -> JSONResponse:
    """
    ### [Base]전용 문서 삭제
    미니오에 저장된 document를 삭제합니다.
    """
    # 시작 시간 측정
    request_datetime = datetime.now()

    document_id:str = inputs.get("document_id")
    document_name:str = inputs.get("document_name")

    response: dict = dict(resource_id=dict())
    response_log: dict = dict()
    request_datetime = datetime.now()
    
    # 문서 저장(minio or local pc)
    delete_success = delete_document(document_id, document_name)

    # 문서 저장에 실패하였을 경우 "문서 정보를 저장하는 중 에러가 발생했습니다" Error return
    if not delete_success:
        status_code, error = ErrorResponse.ErrorCode.get(4103)
        error.error_message = error.error_message.format("문서")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # 종료 시간 측정 
    response_datetime = datetime.now()
    # 걸린 시간 측정 (종료시간 - 시작시간)
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    # response log 생성(시작시간, 종료시간, 걸린시간)
    response_log.update(
        dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        )
    )
    
    # response 객체 생성
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
    )

    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.post("/docx/cls-kv")
async def post_upload_document_cls_kv(
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [Base]전용 문서 업로드 후 cls -> kv 진행 API
    base64encoding된 문서 data와 문서 파일명을 토대로 적재(minio or local)후 DB에 Document Info Insert<br>
    그 후 cls 및 kv 진행하여 return
    """
    # 한국평가용, 나중에는 /inference/docx-cls-kv로 변경 필요
    # 시작 시간 측정
    request_datetime = datetime.now()

    docx_upload_param = dict(
        current_user = current_user,
        session = session,
        document_name = inputs.get('document_name'),
        document_data = inputs.get('document_data'),
        document_path = inputs.get('document_path'),
    )

    # 1. 문서 업로드
    docx_upload_result = docx.upload_docx(inputs = docx_upload_param)
    if(type(docx_upload_result) is JSONResponse):
        return docx_upload_result

    docx_info = {x.name: getattr(docx_upload_result, x.name) for x in docx_upload_result.__table__.columns}
    docx_id = docx_info.get('document_id', '')
    inputs['document_id'] = docx_id


    # 2. cls진행
    # doc_type을 미리 사전지식으로 parameter에서 알려주고 use 및 trust가 true일경우 이 작업 생략 
    # inputs['is_call_function'] = True    
    # if(
    #     inputs['hint']['doc_type']['doc_type'] 
    #     and inputs['hint']['doc_type']['use'] 
    #     and inputs['hint']['doc_type']['trust']):
    #     pass
    # else:
    #     inputs['route_name'] = 'cls'
    #     cls_response = ocr(request=request, inputs=inputs, current_user=current_user, session=session)
    #     if(type(cls_response) is JSONResponse): return cls_response 
    #     cls_result = cls_response.get("inference_results", {})
    #     doc_type = cls_result.get("doc_type","")
    #     inputs['doc_type'] = doc_type.get('doc_type_code')
    #     inputs['cls_result'] = {
    #         'score': cls_result.get('cls_score'),
    #         'doc_type': doc_type.get('doc_type_code')
    #     }

    # 3. kv진행
    inputs['is_call_function'] = True
    inputs['route_name'] = 'kv' 
    kv_response = ocr(request=request, inputs=inputs, current_user=current_user, session=session)
    if(type(kv_response) is JSONResponse): return kv_response
    kv_response.update(
        document_info = docx_info
    )
    return JSONResponse(content=jsonable_encoder(kv_response))
    
    
@router.post("/inference/docx-cls-kv")
async def post_inference_docx_cls_kv(
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [Base]전용 문서 업로드 후 cls -> kv 진행 API
    base64encoding된 문서 data와 문서 파일명을 토대로 적재(minio or local)후 DB에 Document Info Insert<br>
    그 후 cls 및 kv 진행하여 return
    """
    # 한국평가용, 나중에는 /inference/docx-cls-kv로 변경 필요
    # 시작 시간 측정
    request_datetime = datetime.now()

    docx_upload_param = dict(
        current_user = current_user,
        session = session,
        document_name = inputs.get('document_name'),
        document_data = inputs.get('document_data'),
        document_path = inputs.get('document_path'),
    )

    # 1. 문서 업로드
    
    upload_document = False
    if upload_document:
        docx_upload_result = docx.upload_docx(inputs = docx_upload_param)
    else: 
        docx_upload_result = docx.upload_docx(inputs = docx_upload_param, upload_document = False)
    if(type(docx_upload_result) is JSONResponse):
        return docx_upload_result

    docx_info = {x.name: getattr(docx_upload_result, x.name) for x in docx_upload_result.__table__.columns}
    docx_id = docx_info.get('document_id', '')
    inputs['document_id'] = docx_id
    

    # 2. cls진행
    # doc_type을 미리 사전지식으로 parameter에서 알려주고 use 및 trust가 true일경우 이 작업 생략 
    # inputs['is_call_function'] = True    
    # if(
    #     inputs['hint']['doc_type']['doc_type'] 
    #     and inputs['hint']['doc_type']['use'] 
    #     and inputs['hint']['doc_type']['trust']):
    #     pass
    # else:
    #     inputs['route_name'] = 'cls'
    #     cls_response = ocr(request=request, inputs=inputs, current_user=current_user, session=session)
    #     if(type(cls_response) is JSONResponse): return cls_response 
    #     cls_result = cls_response.get("inference_results", {})
    #     doc_type = cls_result.get("doc_type","")
    #     inputs['doc_type'] = doc_type.get('doc_type_code')
    #     inputs['cls_result'] = {
    #         'score': cls_result.get('cls_score'),
    #         'doc_type': doc_type.get('doc_type_code')
    #     }

    # 3. kv진행
    inputs['is_call_function'] = True
    inputs['route_name'] = 'kv' 
    if inputs.get('document').get('file'):
        inputs['image_bytes'] = inputs['document']['file']
        inputs['document_path'] = inputs['document']['file_path']
        del inputs['document']
    kv_response = await ocr(request=request, inputs=inputs, current_user=current_user, session=session)
    if(type(kv_response) is JSONResponse): return kv_response
    kv_response.update(
        document_info = docx_info
    )
    return JSONResponse(content=jsonable_encoder(kv_response))
    

