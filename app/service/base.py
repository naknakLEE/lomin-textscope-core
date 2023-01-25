import typing as t

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import OAuth2PasswordRequestForm, UserInfo as UserInfoInModel
from fastapi.encoders import jsonable_encoder

from app.common.const import get_settings
from app.utils.auth import authenticate_user, create_access_token
from app.utils.logging import logger

from app.utils.document import (
    delete_document,
    get_page_count,
    is_support_format,
    save_upload_document,
)
from app.schemas import error_models as ErrorResponse
from app.utils.utils import cal_time_elapsed_seconds, get_ts_uuid
from app.database.connection import db 
from app.database import query, schema

settings = get_settings()   # default setting

async def post_auth_token(
    inputs: OAuth2PasswordRequestForm,
    session: Session,    
):
    """
        ### [Base] OAuth2.0 토큰 발급
        입력받은 Email을 토대로 OAuth2.0 토큰을 생성후 Return
    """
    
    user = authenticate_user(inputs.email, inputs.password, session)
    if user is None:
        status_code, error = ErrorResponse.ErrorCode.get(2401)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))

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
    
async def post_upload_document(
    inputs: t.Dict,
    current_user: UserInfoInModel,
    session: Session
):
    """
    ### [Base] 문서 업로드
    base64encoding된 문서 data와 문서 파일명을 토대로 적재(minio or local)후 DB에 Document Info Insert<br>
    문서 고유 ID(document_id) return
    """
    
    # 시작 시간 측정
    request_datetime = datetime.now()

    user_email:    str    = current_user.email
    document_id:   str    = inputs.get("document_id")
    document_name: str    = inputs.get("document_name")
    document_data: str    = inputs.get("document_data")
    
    response: dict = dict()
    response_log: dict = dict()
    
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
    # 고객사에서 document_id를 지정해서 보내줄 경우 해당 아이디가 minio, DB에 들어가도록 처리
    document_id = document_id if document_id else get_ts_uuid("document")
    logger.info("start upload docx (document_id: {})", document_id)

    # 문서 저장에 성공했을시, document 테이블에 insert        
    document_pages, document_name = get_page_count(document_data, document_name)

    # 문서 저장(minio or local pc)
    save_success, save_path = save_upload_document(document_id, document_name, document_data)

    # 문서 저장에 실패하였을 경우 "문서 정보를 저장하는 중 에러가 발생했습니다" Error return
    if not save_success:
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    logger.info(f"success save document document_id : {document_id}")
    # 기존 document insert에서 document_description, doc_type_idx, document_type 제외
    dao_document_params = {
        "document_id": document_id,
        "user_email": user_email,
        "user_team": user_team,
        "document_id":document_id,
        "document_path": save_path,
        "document_pages": document_pages
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
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed
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


async def post_delete_document(
    inputs: t.Dict,
    session: Session
):
    """
        ### [Base] 문서 삭제
        미니오에 저장된 document를 삭제합니다.
    """
    # 시작 시간 측정
    request_datetime = datetime.now()

    document_id:   str = inputs.get("document_id")
    # document_name: str = inputs.get("document_name")

    response: dict = dict()
    response_log: dict = dict()
    request_datetime = datetime.now()
    
    select_document_result = query.select_document(session, document_id=document_id, is_used=True)
    # document_id에 해당하는 문서가 없을 경우 Error return
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 문서 삭제(minio or local pc)
    delete_success = delete_document(document_id, select_document_result.document_path)
    
    # is_used True -> False
    _ = query.update_document(session, document_id=document_id, is_used=False)
    
    # 문서 삭제에 실패하였을 경우 "문서를 삭제하는 중 에러가 발생했습니다" Error return
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
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed
    )
    
    # response 객체 생성
    response.update(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        response_log=response_log,
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))