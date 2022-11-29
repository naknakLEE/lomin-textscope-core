
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app import hydra_cfg
from app.models import UserInfo as UserInfoInModel
from app.database.connection import db 
from app.service import front
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashbaord_info(
    date_start: Optional[str] = Query(None, description = "조회 시작 일자, YYYY.MM.DD"),
    date_end: Optional[str] = Query(None, description = "조회 마지막 일자, YYYY.MM.DD"),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    
    return front.get_dashbaord_info(session, date_start=date_start, date_end=date_end)        