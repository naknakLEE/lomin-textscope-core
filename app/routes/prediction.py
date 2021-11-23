import requests
import base64
import zipfile
import os

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
    
    # @TODO: select all image ids
    
    # @TODO: select all prediction data
    dao_result_list = query.select_inference_all(session)
    for res in dao_result_list:
        doc_type =  models.DocType(
            code= res.Category.category_code,
            name= res.Category.category_name_kr,
            confidence=0.98,
            is_hint_used=False,
            is_hint_trusted=False
        )

    doc_type = models.DocType(
        code="A01",
        name="주민등록증",
        confidence=0.98,
        is_hint_used=False,
        is_hint_trusted=False
    )
    
    test_doc_type = models.DocType(
        code="A02",
        name="통장사본",
        confidence=0.98,
        is_hint_used=False,
        is_hint_trusted=False
    )
    
    bbox = models.Bbox(
        x=123.0,
        y=321.0,
        w=111.2,
        h=222.3
    )
    
    key_values = [
        models.KeyValue(
            id="kv-001",
            key="주소",
            confidence=0.78,
            text_ids=['txt-0001'],
            text="서울특별시 서초구 서초대로 396",
            bbox=bbox,
            is_hint_used=False,
            is_hint_trusted=False
        ),
        models.KeyValue(
            id="kv-002",
            key="생년월일",
            confidence=0.83,
            text_ids=['txt-0002'],
            text="1993-12-05",
            bbox=bbox,
            is_hint_used=True,
            is_hint_trusted=False
        ),
    ]
    
    test_key_values = [
        models.KeyValue(
            id="kv-001",
            key="주소",
            confidence=0.78,
            text_ids=['txt-0001'],
            text="서울시 성동구",
            bbox=bbox,
            is_hint_used=False,
            is_hint_trusted=False
        ),
        models.KeyValue(
            id="kv-002",
            key="계좌번호",
            confidence=0.83,
            text_ids=['txt-0002'],
            text="110-234-234623",
            bbox=bbox,
            is_hint_used=True,
            is_hint_trusted=False
        ),
    ]
    
    texts = [
        models.Text(
            id="txt-0001",
            text="홍길동",
            bbox=bbox,
            confidence=0.87,
            kv_ids=['kv-001']
        ),
        models.Text(
            id="txt-0002",
            text="김철수",
            bbox=bbox,
            confidence=0.94,
            kv_ids=['kv-002']
        ),
    ]
    
    test_texts = [
        models.Text(
            id="txt-0001",
            text="신한은행",
            bbox=bbox,
            confidence=0.87,
            kv_ids=['kv-001']
        ),
        models.Text(
            id="txt-0002",
            text="통장발급",
            bbox=bbox,
            confidence=0.94,
            kv_ids=['kv-002']
        ),
    ]
    
    test_image_paths = [
        '/test/file/test_file_image1.jpg',
        '/test/file/test_file_image2.jpg'
    ]
    
    """Query
    SELECT inference.*, image.image_path as image_path
    FROM inference
    LEFT JOIN image on image.image_pkey = inference.image_pkey;
    """
    
    predictions = [
        {
            "image_path": test_image_paths[0],
            "inference_result": models.BaseTextsResponse(
                texts=texts
            ),
            "inference_type": "gocr"
        },
        {
            "image_path": test_image_paths[1],
            "inference_result": models.PredictionResponse(
                doc_type=test_doc_type,
                key_values=test_key_values,
                texts=test_texts
            ),
            "inference_type": "kv"
        }
    ]
    
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
    
    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)[0]
    # inference_img_paths = inference_img_path.split(".")[-1]

    inference_img_path = Path(inference_img_path)
    inference_img_path = str(inference_img_path.parents[0]) + '/' + inference_img_path.stem + '_debug' + inference_img_path.suffix
    img_str = load_image2base64(inference_img_path)

    # @TODO: select image file from db
    image = None
    
    if visualize:
        # @TODO: load image file
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
    
    
    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)[0]
    inference_img_path = Path(inference_img_path)
    inference_img_path = str(inference_img_path.parents[0]) + '/' + inference_img_path.stem + '_debug' + inference_img_path.suffix

    img_str = load_image2base64(inference_img_path)

    # @TODO: select image file from db
    image = img_str
    
    if visualize:
        # @TODO: load image file
        image = image
    
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