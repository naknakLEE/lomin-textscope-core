# import os
import requests
# import numpy as np
# import cv2

from fastapi import Depends, File, UploadFile, APIRouter
from sqlalchemy.orm import Session

from app.models import User
from app.database.schema import Usage
from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings


settings = get_settings()
router = APIRouter()


@router.post("/inference")
async def inference(session: Session = Depends(db.session), current_user: User = Depends(get_current_active_user), file: UploadFile = File(...)):
    test_url = f'http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference'

    image_data = await file.read()
    response = requests.post(test_url, data=image_data)

    Usage.create_usage(session, auto_commit=True, email=current_user.email, status_code=response.status_code)

    return response.json()



