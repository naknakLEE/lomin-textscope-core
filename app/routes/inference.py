# import os
import requests
# import numpy as np
# import cv2

from fastapi import Depends, File, UploadFile, APIRouter
from sqlalchemy.orm import Session

from models import User
from database.schema import Usage
from database.connection import db
from utils.authorization import get_current_active_user
from common.const import get_settings


settings = get_settings()
router = APIRouter()


@router.post("/inference")
# def inference(file: UploadFile = File(...)):
def inference(session: Session = Depends(db.session), current_user: User = Depends(get_current_active_user), file: UploadFile = File(...)):
    test_url = f'http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference'

    image_data = file.file.read()
    # nparr = np.fromstring(image_data, np.uint8)
    # image_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # _, img_encoded = cv2.imencode('.jpg', image_data)
    # image_data = img_encoded.tobytes()

    response = requests.post(test_url, data=image_data)

    # session 생성해서 사용하는 것은 병목이 될 수 있으니
    # redis나 memchached같은 change storage를 사용하는게 어떤가
    # session = next(db.session())
    Usage.create(session, auto_commit=True, email=current_user.email, status_code=response.status_code)
    # session.close()

    return response.json()
