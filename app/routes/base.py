import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import OAuth2PasswordRequestForm, UserInfo as UserInfoInModel
from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from app import hydra_cfg
from app.common.const import get_settings
from app.utils.auth import authenticate_user, create_access_token
from app.utils.logging import logger

from app.utils.document import (
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
    inputs: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    """
    ### [Base]전용 OAuth2.0 토큰 발급
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
    document_path:str = inputs.get("document_path")    

    logger.info("#0-1 start upload document at {}", datetime.now())
    logger.info("#0-2 document_name: {}, len(document_data): {}, document_path {}", document_name, len(document_data), document_path)

    response: dict = dict(resource_id=dict())
    response_log: dict = dict()
    request_datetime = datetime.now()

    # [20220824_박일우] 파일이 아닌 Path로 파라미터가 넘어올경우 Path에 연결 후 document 가져오기
    if document_data is None and document_path is not None:
        file_path = Path(document_path)
        document_name = file_path.name
        path_verify = document_path_verify(document_path)
        if isinstance(path_verify, JSONResponse): return path_verify
        
        with file_path.open('rb') as file:
            document_data = file.read()
            document_data = base64.b64encode(document_data)    
    
    # 업로드된 파일 포맷(확장자) 확인
    logger.info("[{}] #1-1 try check support format", datetime.now())
    is_support = is_support_format(document_name)
    logger.info("[{}] #1-2 end check support format (suport: {})", datetime.now(), is_support)
    
    # 지원하지 않은 포맷(확장자)일시 "지원하지 않는 파일 형식입니다" Error return
    if is_support is False:
        status_code, error = ErrorResponse.ErrorCode.get(2105)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # 유저 정보 확인(Document Info Insert시 유저 정보가 필요하여서 실행함..)
    logger.info("[{}] #2-1 try select user_email from db", datetime.now())
    select_user_result = query.select_user(session, user_email=user_email)
    logger.info("[{}] #2-2 end select user_email from db (user_info: {})", datetime.now(), type(select_user_result))
    
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team        

    # 고유한 document_id 생성 -> DB적재용이 아닌 path를 만들기 위함!
    document_id = get_ts_uuid("document")

    # 문서 저장(minio or local pc)
    logger.info("[{}] #3-1 try save or upload documnet", datetime.now())
    save_success, save_path = save_upload_document(document_id, document_name, document_data)
    logger.info("[{}] #3-2 end save or upload documnet (save_success: {})", datetime.now(), save_success)

    # 문서 저장에 실패하였을 경우 "문서 정보를 저장하는 중 에러가 발생했습니다" Error return
    if not save_success:
        status_code, error = ErrorResponse.ErrorCode.get(4102)
        error.error_message = error.error_message.format("문서")
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

    # 문서 저장에 성공했을시, document 테이블에 insert        
    logger.info("[{}] #4-1 try get page count", datetime.now())
    document_pages = get_page_count(document_data, document_name)
    logger.info("[{}] #4-2 end get page cunt (document_pages: {})", datetime.now(), document_pages)
    
    logger.info(f"success save document document_id : {document_id}")
    # 기존 document insert에서 document_description, doc_type_idx, document_type 제외
    dao_document_params = {
        "document_id": document_id,
        "user_email": user_email,
        "user_team": user_team,
        "document_path": save_path,
        "document_pages": document_pages,
    }
    
    logger.info("[{}] #5-1 try insert documnet info to db", datetime.now())
    insert_document_result = query.insert_document(session, **dao_document_params)
    logger.info("[{}] #5-2 try insert documnet info to db (result: {})", datetime.now(), insert_document_result)
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

    logger.info("#6-1 upload document end at {}", datetime.now())
    logger.info("#6-2 end document_id: {}", document_id)

    return JSONResponse(status_code=200, content=jsonable_encoder(response))
