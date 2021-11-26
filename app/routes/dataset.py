import requests
import base64
import zipfile
import os
import uuid

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
from app.utils.utils import cal_time_elapsed_seconds
from app.database import query


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
    
    # @TODO: db insert dataset info
    dao_dataset_params = {
        'dataset_id': inputs.get('dataset_id'), 
        'root_path': str(images_path),
        'zip_file_name': zip_file_name     
        }
    dataset_pkey, dataset_id = query.insert_training_dataset(session, **dao_dataset_params)
    new_categories = list(save_path.parent.joinpath(zip_file_name).iterdir())
    support_set_path = Path(settings.SUPPORT_SET_DIR)
    pretrained_categories = [d for d in support_set_path.iterdir() if d.is_dir()]
    
    exist_category_list = query.select_category_all(session)
    exist_category_name_list = [category.category_name_en for category in exist_category_list]
    
    if not exist_category_list:
        for category in pretrained_categories:
            dao_category_params = {
                'category_name_en': category.name,
                'category_code': 'P01',
                'is_pretrained': True
            }
            category_pkey = query.insert_category(session, **dao_category_params)

        
    for category in new_categories:
        if category.name not in exist_category_name_list:
            dao_category_params = {
                'category_name_en': category.name,
                'category_code': 'A01',
                'is_pretrained': False
            }
            category_pkey = query.insert_category(session, **dao_category_params)
        else:
            category_pkey = query.select_category_by_name(session, category_name=category.name)

        for image in images:
            if str(image).find(category.name) != -1:
                dao_image_params = {
                    'image_id': str(uuid.uuid4()),
                    'image_path': str(image),
                    'category_pkey': category_pkey,
                    'dataset_pkey': dataset_pkey,
                    'image_type': 'training'
                }
                image_pkey = query.insert_image(session, **dao_image_params)
            

    
    # validation inspect image files
    for image in images:
        category = image.stem
        ext = image.suffix[1:] # e.g. '.jpg'
        if ext in settings.IMAGE_VALIDATION:
            # @TODO: db insert images info
            pass
    
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        is_exist=is_exist,
        image_list=images
    ))
    
    response.update(dict(
        response_log=response_log
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.get("/cls")
def get_cls_train_dataset(
    dataset_id: str,
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    request_datetime = datetime.now()
    response_log = dict()

    # @TODO: select db by dataset_id
    dao_object = query.select_category(session, dataset_id)

    datasets = []
    for do in dao_object:
        datasets.append(models.Dataset(
            image_id=do.Image.image_id,
            category_id=do.Category.category_name_en,
            category_name=do.Category.category_name_en,
            filename=(do.Image.image_path).split("/")[-1]
        ))
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(dict(
        dataset=datasets,
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed
    ))
    response.update(dict(
        dataset=datasets,
        response_log=response_log
    ))

    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.delete('/cls')
def delete_cls_train_dataset(
    dataset_id: str,
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    request_datetime = datetime.now()
    response_log = dict()
    
    target_dataset = query.select_dataset(session, dataset_id=dataset_id)[0]
    
    target_path = Path(target_dataset.root_path)
    
    is_exist = target_path.exists()
    images = list()
    if is_exist:
        images = list(target_path.glob('**/*.*'))
        dirs = [d for d in target_path.iterdir() if d.is_dir()]
        response_log.update(dict(
            images=[],
            dirs=[]
        ))
        for image in images:
            response_log['images'].append(str(image))
            try:
                os.remove(image)
            except:
                # @TODO: not exists file exception
                pass
        for d in dirs:
            response_log['dirs'].append(str(d))
            try:
                d.rmdir()
                pass
            except:
                # @TODO: directory not empty or directory not exists
                pass
        # remove root path
        target_path.rmdir()
    else:
        # @TODO: target dataset directory가 없을 경우에 대한 exception raise
        pass
    
    query_result = query.delete_category_cascade_image(session, dataset_pkey=target_dataset.dataset_pkey)
    res = query.delete_dataset(session, dataset_id)
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed
    ))
    
    response.update(dict(
        response_log=response_log
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))