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
from pathlib import Path

from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from app import models
from sqlalchemy.orm import Session
from app.utils.utils import cal_time_elapsed_seconds
from app.database import query
from app.utils.utils import load_image2base64, basic_time_formatter


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
    
    gocr_results = query.select_inference_by_type(session, inference_type='gocr')
    kv_results = query.select_inference_by_type(session, inference_type='kv')
    
    for gocr_res in gocr_results:
        inference_result = gocr_res.inference_result
        inference_type = gocr_res.inference_type
        image_pkey = gocr_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        image_path = image.image_path
        
        texts = list()
        for text_, box_, score_, class_ in zip(inference_result["texts"], inference_result["boxes"], inference_result["scores"], inference_result["classes"]):
            bbox = models.Bbox(
                x=box_[0],
                y=box_[1],
                w=box_[2] - box_[0],
                h=box_[3] - box_[1],
            )
            # TODO: kv_ids 매핑 필요
            text = models.Text(
                id=class_,
                text=text_,
                bbox=bbox,
                confidence=score_,
                kv_ids=[class_]
            )
            texts.append(text)
        
        prediction = dict(
            image_path=image_path,
            inference_result=dict(
                texts=texts
            ),
            inference_type=inference_type
        )
        predictions.append(prediction)
        
    for kv_res in kv_results:
        inference_result = kv_res.inference_result
        inference_type = kv_res.inference_type
        image_pkey = kv_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        category = query.select_category_by_pkey(session, category_pkey=image.category_pkey)
        image_path = image.image_path
        image_category = category.category_name_en
        kv = inference_result.get('kv', {})
        key_values = list()
        texts = list()
        
        for key, value in kv.items():
            if not key.endswith("_pred") or not value: continue
            bbox = models.Bbox(
                x=value["box"][0],
                y=value["box"][1],
                w=value["box"][2] - value["box"][0],
                h=value["box"][3] - value["box"][1],
            )
            # TODO: key, kv_ids 매핑 필요
            key_value = models.KeyValue(
                id=value["class"],
                key=key,
                confidence=value["score"],
                text=value["value"],
                bbox=bbox,
                is_hint_used=False,
                is_hint_trusted=False,
            )
            key_values.append(key_value)

        texts = list()
        for text_, box_, score_, class_ in zip(inference_result["texts"], inference_result["boxes"], inference_result["scores"], inference_result["classes"]):
            bbox = models.Bbox(
                x=box_[0],
                y=box_[1],
                w=box_[2] - box_[0],
                h=box_[3] - box_[1],
            )
            # TODO: kv_ids 매핑 필요
            text = models.Text(
                id=class_,
                text=text_,
                bbox=bbox,
                confidence=score_,
                kv_ids=[class_]
            )
            texts.append(text)

                
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
    
    kv_result = query.select_kv_inference_from_taskid(session, task_id=task_id)
    inference_type = kv_result.inference_type
    inference_result = kv_result.inference_result
    response_log = inference_result.get('response_log')
    started_datetime = basic_time_formatter(response_log.get('time_textscope_request'))
    finished_datetime = basic_time_formatter(response_log.get('time_textscope_response'))
    kv = inference_result.get(inference_type)
    
    doc_type = models.DocType(
        code=inference_result.get('doc_type').split('_')[0],
        name=inference_result.get('doc_type').split('_')[-1],
        confidence=0.93,
        is_hint_used=False,
        is_hint_trusted=False
    )
    key_values = list()
    texts = list()
    
    inference_result = kv_result.inference_result
    kv = inference_result.get("kv", {})

    key_values = list()
    for key, value in kv.items():
        if not key.endswith("_pred") or not value: continue
        bbox = models.Bbox(
            x=value["box"][0],
            y=value["box"][1],
            w=value["box"][2] - value["box"][0],
            h=value["box"][3] - value["box"][1],
        )
        # TODO: key, kv_ids 매핑 필요
        key_value = models.KeyValue(
            id=value["class"],
            key=key,
            confidence=value["score"],
            text=value["value"],
            bbox=bbox,
            is_hint_used=False,
            is_hint_trusted=False,
        )
        key_values.append(key_value)
        
    prediction = models.PredictionResponse(
        doc_type=doc_type,
        key_values=key_values,
        texts=texts
    )
    
    # @TODO: select task status from db
    task = models.Task(
        task_id=task_id,
        status_code='ST-TRN-CLS-0003',
        status_message='학습 task 완료',
        progress=1.0,
        started_datetime=started_datetime,
        finished_datetime=finished_datetime
    )
    
    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)[0]
    img_str = load_image2base64(inference_img_path)

    image = None
    
    if visualize:
        image = img_str
    
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
    
    text = models.Text()
    
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
    
    
    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)[0]
    img_str = load_image2base64(inference_img_path)

    image = None
    
    if visualize:
        image = img_str
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