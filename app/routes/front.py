
from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.utils.auth import get_current_active_user as get_current_active_user
from app.models import UserInfo as UserInfoInModel
from app.database.connection import db 
from app.service import front

router = APIRouter()

@router.get("/task")
async def get_task_list(
    document_name: Optional[str]   = Query(None, description = "문서명(문서명으로 검색시 사용)"),
    date_start:    Optional[str]   = Query(None, description = "조회 시작 일자, YYYY.MM.DD"),
    date_end:      Optional[str]   = Query(None, description = "조회 마지막 일자, YYYY.MM.DD"),
    rows_limit:    int             = Query(..., description = "가져올 총 업무 수, 최대 1000"),
    rows_offset:   int             = Query(..., description = "로우 오프셋"),
    current_user:  UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    
    return front.get_task_list(session, document_name=document_name, date_start=date_start, date_end=date_end, rows_limit=rows_limit, rows_offset=rows_offset)

@router.get("/task/{inference_id}")
async def get_task_info(
    inference_id: str = Path(None, description="추론 고유 아이디"),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    
    return front.get_task_info(session, inference_id)

@router.get("/dashboard")
async def get_dashbaord_info(
    date_start: Optional[str] = Query(None, description = "조회 시작 일자, YYYY.MM.DD"),
    date_end: Optional[str] = Query(None, description = "조회 마지막 일자, YYYY.MM.DD"),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),    
) -> JSONResponse:
    
    return front.get_dashbaord_info(session, date_start=date_start, date_end=date_end)        