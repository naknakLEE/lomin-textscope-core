from typing import Any
from fastapi import APIRouter, Depends, Body, Request
from fastapi import BackgroundTasks
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import (
    HTTPBearer
)

from app.config import hydra_cfg
from app.database.connection import db
from app.models import UserInfo as UserInfoInModel
from app.common.const import get_settings
from app import models
from app.schemas import HTTPBearerFake

from app.service.index import (
    check_status as check_status_service,
    get_image as get_image_service,
    post_upload_document as post_upload_document_service,
    post_document_image_crop as post_document_image_crop_service
    
)
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


settings = get_settings()
router = APIRouter()
security = HTTPBearer() if hydra_cfg.route.use_token else HTTPBearerFake()


@router.get("/status", response_model=models.StatusResponse)
def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    -  is_pp_server_working: 후처리 서버와 연결 상태 확인
    """
    return check_status_service()

@router.get("/docx")
def get_image(
    document_id: str,
    page: int = 1,
    rotate: bool = False,
    session: Session = Depends(db.session)
) -> JSONResponse:
    return get_image_service(
        document_id = document_id, 
        page = page, 
        rotate = rotate, 
        session = session
    )

@router.post("/docx")
async def post_upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserInfoInModel = Depends(get_current_active_user),
    params: dict = Body(...), 
    session: Session = Depends(db.session),
) -> JSONResponse:
    
    return await post_upload_document_service(
        request = request,
        background_tasks = background_tasks,
        current_user = current_user,
        params = params,
        session = session
    )

@router.post("/image/crop")
def image_crop(
    params: models.ParamPostImageCrop,
    session: Session = Depends(db.session)
) -> JSONResponse:
    return post_document_image_crop_service(
        params = params,
        session = session
    )