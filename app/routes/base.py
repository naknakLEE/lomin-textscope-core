import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.models import OAuth2PasswordRequestForm, UserInfo as UserInfoInModel
from fastapi import APIRouter, Body, Depends, Request
from app.config import hydra_cfg
from app.common.const import get_settings
from app.utils.logging import logger
from app.utils.minio import MinioService
from app.database.connection import db 
from app.service.base import (
    post_auth_token as post_auth_token_service,
    post_upload_document as post_upload_document_service,
    post_delete_document as post_delete_document_service
)

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
    ### [Base] OAuth2.0 토큰 발급
    입력받은 Email을 토대로 OAuth2.0 토큰을 생성후 Return
    """
    
    return await post_auth_token_service(
        inputs = inputs,
        session = session
    )

@router.post("/docx")
async def post_upload_document(
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    ### [Base] 문서 업로드
    base64encoding된 문서 data와 문서 파일명을 토대로 적재(minio or local)후 DB에 Document Info Insert<br>
    문서 고유 ID(document_id) return
    """
    return await post_upload_document_service(
        inputs = inputs,
        current_user = current_user,
        session = session
    )
    

@router.post("/docx/delete")
async def post_delete_document(
    inputs: Dict = Body(...),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    ### [Base] 문서 삭제
    미니오에 저장된 document를 삭제합니다.
    """
    return await post_delete_document_service(
        inputs = inputs,
        session = session
    )
