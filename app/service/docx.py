
import base64
from pathlib import Path
from typing import Dict
from fastapi import  Body
from starlette.responses import JSONResponse
from app.database.connection import db 
from app.database import query, schema
from sqlalchemy.orm import Session

from app.utils.logging import logger
from app.utils.document import document_path_verify, get_page_count, is_support_format, save_upload_document
from app.schemas import error_models as ErrorResponse
from fastapi.encoders import jsonable_encoder

from app.utils.utils import get_ts_uuid

def upload_docx(
    inputs: Dict,
    upload_document: bool = True
):
    user_email:str    = inputs.get("current_user").__getattribute__('email')
    document_name:str = inputs.get("document_name")
    document_data:str = inputs.get("document_data")
    document_path:str = inputs.get("document_path")
    session: Session  = inputs.get("session")
    
    save_path = None
    document_pages = None

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
    if document_name:
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
    if upload_document:
        save_success, save_path = save_upload_document(document_id, document_name, document_data)

        # 문서 저장에 실패하였을 경우 "문서 정보를 저장하는 중 에러가 발생했습니다" Error return
        if not save_success:
            status_code, error = ErrorResponse.ErrorCode.get(4102)
            error.error_message = error.error_message.format("문서")
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

        # 문서 저장에 성공했을시, document 테이블에 insert        
        document_pages = get_page_count(document_data, document_name)
        logger.info(f"success save document document_id : {document_id}")
    # 기존 document insert에서 document_description, doc_type_idx, document_type 제외
    dao_document_params = {
        "document_id": document_id,
        "user_email": user_email,
        "user_team": user_team,
        "document_path": save_path if save_path else "",
        "document_pages": document_pages if document_pages else 0,
    }
    insert_document_result = query.insert_document(session, **dao_document_params)

    return insert_document_result        