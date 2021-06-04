from datetime import datetime
import requests

from fastapi import Depends, File, UploadFile, APIRouter, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.models import User
from app.database.schema import Usage
from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
from app.errors import exceptions as ex


settings = get_settings()
router = APIRouter()


@router.post("")
async def inference(session: Session = Depends(db.session), current_user: User = Depends(get_current_active_user), file: UploadFile = File(...)):
    test_url = f'http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference'

    image_data = await file.read()
    response = requests.post(test_url, data=image_data)

    return response.json()


@router.get("/usage")
def read_usage(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_multi(session, skip=skip, limit=limit)
    return usages


@router.get("/usage/{user_email}")
def read_usage_by_email(
    user_email: EmailStr,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_by_email(session, email=user_email)
    return usages


@router.get("/count")
def count_usage(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage(session)
    return usages


@router.get("/count/{user_email}")
def count_usage_by_email(
    user_email: EmailStr,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    usages = Usage.get_usage(session, email=user_email)

    successed_count = len(usages["success_response"])
    failed_count = len(usages["failed_response"])
    return { 
        "total_count": successed_count + failed_count,
        "success_count":successed_count, 
        "fail_count": failed_count,
    }