import requests
import base64
import zipfile
import os
import pandas as pd
import json

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
from app.utils.utils import load_image2base64


settings = get_settings()
router = APIRouter()

@router.get('/')
def get_all_prediction(
    session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    predictions = list()
    
    local_category_path = Path(settings.CATEGORY_PATH).joinpath('categories.csv')
    categories = dict()
    csv_file = pd.read_csv(local_category_path)
    for name, pkey, *_ in zip(*[csv_file[k] for k in csv_file.columns]):
        categories[name] = pkey
        categories[pkey] = name
    
    # @TODO: select all image ids
    gocr_results = query.select_inference_by_type(session, inference_type='gocr')
    kv_results = query.select_inference_by_type(session, inference_type='kv')
    
    for gocr_res in gocr_results:
        inference_result = gocr_res.inference_result
        inference_type = gocr_res.inference_type
        image_pkey = gocr_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        if image.category_pkey is None:
            continue
        image_path = image.image_path
        
        prediction = dict(
            image_path=image_path,
            inference_result=dict(
                texts=inference_result.get('texts')
            ),
            inference_type=inference_type
        )
        predictions.append(prediction)
        
    for kv_res in kv_results:
        inference_result = kv_res.inference_result
        inference_type = kv_res.inference_type
        classes = list(set(inference_result.get('classes', [])))
        image_pkey = kv_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        if image.category_pkey is None:
            continue
        image_path = image.image_path
        image_category = categories[image.category_pkey]
        logger.info(f'image_category {image_category}')
        kv = inference_result.get('kv', {})
        key_values = list()
        texts = list()
        
        for cls in classes:
            kv_data = kv.get(f'{cls}_pred')
            key_value_model = models.KeyValue(
                id='test_id',
                key=cls,
                confidence=kv_data.get('score'),
                text_ids=[kv_data.get('class')],
                text=kv_data.get('text'),
                bbox=models.Bbox(
                    x=kv_data.get('box')[0],
                    y=kv_data.get('box')[1],
                    w=kv_data.get('box')[2],
                    h=kv_data.get('box')[3],
                ),
                is_hint_used=False,
                is_hint_trusted=False
            )
            key_values.append(key_value_model)
            texts.append(kv_data.get(cls))
                
        prediction = dict(
            image_path=image_path,
            inference_result=dict(
                doc_type=image_category,
                key_values=key_values,
                texts=texts
            ),
            inference_type=inference_type
        )
        predictions.append(prediction)
        
        
    
    # @TODO: select all prediction data
    # dao_result_list = query.select_inference_all(session)
    # for res in dao_result_list:
    #     doc_type =  models.DocType(
    #         code= res.Category.category_code,
    #         name= res.Category.category_name_kr,
    #         confidence=0.98,
    #         is_hint_used=False,
    #         is_hint_trusted=False
    #     )
    
    # predictions = [
    #     {
    #         "image_path": test_image_paths[0],
    #         "inference_result": models.BaseTextsResponse(
    #             texts=texts
    #         ),
    #         "inference_type": "gocr"
    #     },
    #     {
    #         "image_path": test_image_paths[1],
    #         "inference_result": models.PredictionResponse(
    #             doc_type=test_doc_type,
    #             key_values=test_key_values,
    #             texts=test_texts
    #         ),
    #         "inference_type": "kv"
    #     }
    # ]
    
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        predictions=predictions
    ))
    
    response = dict(
        predictions=predictions,
        response_log=response_log
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.get("/cls-kv")
def get_cls_kv_prediction(
    task_id: str,
    visualize: bool,
    session: Session = Depends(db.session)
) -> JSONResponse:
    request_datetime = datetime.now()
    response = dict()
    response_log = dict()
    
    doc_type = models.DocType(
        code='A01',
        name='주민등록증',
        confidence=0.93,
        is_hint_used=False,
        is_hint_trusted=False
    )
    bbox = models.Bbox(
        x=123.0,
        y=452.0,
        w=113.3,
        h=342.2
    )
    key_value = models.KeyValue(
        id='kv-001',
        key='주소',
        confidence=0.93,
        text_ids=['txt-0001'],
        text='서울특별시 서초구 서초대로 396',
        bbox=bbox,
        is_hint_used=False,
        is_hint_trusted=False
    )
    text = models.Text(
        id='txt-0001',
        text='홍길동',
        bbox=bbox,
        confidence=0.4326,
        kv_ids=['kv-001']
    )
    # @TODO: select prediction result from db
    prediction = models.PredictionResponse(
        doc_type=doc_type,
        key_values=[key_value],
        texts=[text]
    )
    
    # @TODO: select task status from db
    task = models.Task(
        task_id=task_id,
        status_code='ST-TRN-CLS-0003',
        status_message='학습 task 완료',
        progress=1.0,
        started_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        finished_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    )
    
    if visualize:
        # @TODO: load image file
        image = Path("/workspace/assets/dumy_images.jpg").open('rb')
        file_data = image.read()
        encoded_file_data = base64.b64encode(file_data)
        image = encoded_file_data
    else:
        image = None
    
    response_datetime=datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        prediction=prediction,
        task=task,
        image=image
    ))
    
    response.update(dict(
        response_log=response_log,
        prediction=prediction,
        task=task,
        image=image
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))

@router.get("/gocr")
def get_cls_kv_prediction(
    task_id: str,
    visualize: bool,
    session: Session = Depends(db.session)
) -> JSONResponse:
    request_datetime = datetime.now()
    response = dict()
    response_log = dict()
    
    text = models.Text(
        
    )
    
    # @TODO: select prediction result from db
    prediction = models.BaseTextsResponse(
        texts=[text]
    )
    
    # @TODO: select task status from db
    task = models.Task(
        task_id=task_id,
        status_code='ST-TRN-CLS-0003',
        status_message='학습 task 완료',
        progress=1.0,
        started_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        finished_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    )
    
    # @TODO: select image file from db
    
    if visualize:
        # @TODO: load image file
        image = Path("/workspace/assets/dumy_images.jpg").open('rb')
        file_data = image.read()
        encoded_file_data = base64.b64encode(file_data)
        image = encoded_file_data
    else:
        image = None
    
    response_datetime=datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    response_log.update(dict(
        request_datetime=request_datetime,
        response_datetime=response_datetime,
        elapsed=elapsed,
        prediction=prediction,
        task=task,
        image=image
    ))
    
    response.update(dict(
        response_log=response_log,
        prediction=prediction,
        task=task,
        image=image
    ))
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))