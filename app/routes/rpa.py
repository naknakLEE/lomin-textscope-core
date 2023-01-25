from typing import Any
from fastapi import Depends, APIRouter, Body, Security
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.utils.auth import get_current_active_user
from app.database.connection import db
from fastapi.security import (HTTPBearer, HTTPAuthorizationCredentials)
from app.service.rpa import (
    get_rpa_template as get_rpa_template_service,
    post_rpa_template as post_rpa_template_service,
    post_rpa as post_rpa_service
)
from app import models

security = HTTPBearer()
router = APIRouter()


@router.get(
    "/template")
def get_rpa_template(
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### rpa 템플릿 조회
    관리자가 아니면 조회 불가능
    """
    return get_rpa_template_service(
        session=session,
        current_user=current_user
    )

@router.post(
    "/template")
def post_rpa_template(
    params: dict = Body(...),
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Any:
    """
    ### rpa 템플릿 수정
    관리자가 아니면 수정 불가능
    """
    return post_rpa_template_service(
        params=params,
        session=session,
        current_user=current_user
    )
    
    

@router.post(
    "/")
async def post_rpa(
    params: dict = Body(...),
    session: Session = Depends(db.session),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: models.UserInfo = Depends(get_current_active_user),
    token: HTTPAuthorizationCredentials = Security(security),
) -> Any:
    """
    ### RPA 전송을 수동으로 진행합니다.
    
    문서 종류 해외 투자 신고서류에 한에서만 RPA 전송이 이루어집니다.
    
    해외 투자 신고서류 이외의 파일이 들어오면 RPA 전송을 진행하지 않습니다.
    
    """
    return post_rpa_service(
        params=params,
        session=session,
        background_tasks=background_tasks,
        current_user=current_user,
        token=token
    )
