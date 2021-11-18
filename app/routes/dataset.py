import requests
import base64
import zipfile

from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Request, Body, Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from sqlalchemy.orm import Session


settings = get_settings()
router = APIRouter()

@router.post("/cls")
def upload_cls_training_dataset(
    request: dict = Body(...),
    session: Session = Depends(db.session)
) -> JSONResponse:
    inputs = request
    response = dict()
    request_datetime = datetime.now()
    response_log = dict()
    response_log.update(dict(request_datetime=request_datetime))
    encoded_file = inputs.get('file')
    decoded_file = base64.b64decode(encoded_file)
    file_name = inputs.get('file_name')
    save_path = Path(settings.ZIP_PATH) / file_name
    
    Path(settings.ZIP_PATH).mkdir(exist_ok=True)
    
    with save_path.open('wb') as file:
        file.write(decoded_file)
    
    # @TODO: Zip file load and check file integrity
    with zipfile.ZipFile(save_path, 'r') as zip_file:
        zip_file.extractall(save_path.parent)
    
    zip_file_name = Path(file_name).stem
    images_path = save_path.parent / zip_file_name
    is_exist = images_path.exists()
    images = list()
    
    if is_exist:
        images = list(images_path.glob('**/*.*'))
        # @TODO: image file load and check file validation, integrity
    response_log.update(dict(
        is_exist=is_exist,
        image_list=images
    ))
    
    # @TODO: db insert dataset info
    
    # validation inspect image files
    for image in images:
        category = image.stem
        ext = image.suffix[1:] # e.g. '.jpg'
        if ext in settings.IMAGE_VALIDATION:
            # @TODO: db insert images info
            pass
    
    
    response_datetime = datetime.now()
    response_log.update(dict(response_datetime=response_datetime))
    
    response.update(dict(
        response_log=response_log
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))