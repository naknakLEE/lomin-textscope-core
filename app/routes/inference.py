import os
import requests
import numpy as np 
import cv2

from fastapi import Depends, File, UploadFile, APIRouter
from models import User
from utils.authorization import (
    get_current_active_user,
)


router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

SERVING_IP_ADDR = os.getenv('SERVING_IP_ADDR')
SERVING_IP_PORT = os.getenv('SERVING_IP_PORT')


@router.post("/inference") 
def inference(current_user: User = Depends(get_current_active_user), file: UploadFile = File(...)):
    test_url = f'http://{SERVING_IP_ADDR}:{SERVING_IP_PORT}/inference'

    image_data = file.file.read()
    nparr = np.fromstring(image_data, np.uint8)
    image_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    _, img_encoded = cv2.imencode('.jpg', image_data)
    image_data = img_encoded.tobytes()

    files = { 'file': image_data }
    response = requests.post(test_url, data=image_data)

    return response.json()