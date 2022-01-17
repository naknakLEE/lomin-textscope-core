import re
from httpx import Client
from uuid import uuid4

from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Body, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app import models
from app.schemas import inference_responses
from app.utils.utils import (
    set_json_response,
    get_pp_api_name,
    set_ocr_response,
    pretty_dict
)
from app.utils.logging import logger
from app.wrapper import pp, pipeline, settings
from app.database import query
from app.database.connection import db
from app.utils.hint import apply_cls_hint
from app.utils.save_data import (
    save_inference_results,
    save_updated_task
)


router = APIRouter()


"""
### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
입력 데이터: 토큰, ocr에 사용할 파일 <br/>
응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
"""


@router.post("/ocr", status_code=200, responses=inference_responses)
async def ocr(
    background_tasks: BackgroundTasks,
    inputs: Dict = Body(...),
    db: Session = Depends(db.session),
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    start_time = datetime.now()
    request_id = inputs.get("request_id")
    convert_preds_to_texts = inputs.get("convert_preds_to_texts", None)
    post_processing_results = dict()
    response_log = dict()
    response = dict()
    task_id = inputs.get('task_id')
    
    logger.success(f'{task_id}-api request start:\n{pretty_dict(inputs)}')
    
    if settings.DEVELOP:
        if inputs.get("test_doc_type", None) is not None:
            inputs["doc_type"] = inputs["test_doc_type"]
            logger.debug(f'{task_id}-set test doc type: origin doc type={inputs.get("doc_type")}\
                         test doc type={inputs.get("test_doc_type")}')
    
    task_insert_data = models.CreateTask(
        task_id=inputs.get('task_id'),
        image_pkey=inputs.get('image_pkey')
    )
    
    task_insert_result = query.insert_task(db, task_insert_data)
    if not task_insert_result:
        logger.error(f'{task_id}-task id insert error: {pretty_dict(task_insert_data)}')
        error = models.Error(
            error_code="ER-INF-CKV-4003",
            error_message="이미 등록된 task id"
        )
        raise HTTPException(status_code=400, detail=error.dict())
    
    task_pkey = task_insert_result.pkey
    
    with Client() as client:
        # ocr inference
        if settings.USE_OCR_PIPELINE:
            # TODO: sequence_type을 wrapper에서 받도록 수정
            # TODO: python 3.6 버전에서 async profiling 사용에 제한이 있어 sync로 변경했는데 추후 async 사용해 micro bacing 사용하기 위해서는 다시 변경 필요
            status_code, inference_results, response_log = pipeline.multiple(
                client=client, 
                inputs=inputs,
                sequence_type="kv",
                response_log=response_log,
            )
            response_log = dict()
        elif inputs.get("use_heungkuk_life_pipeline_api"):
            status_code, inference_results, response_log = pipeline.single(
                client=client, 
                inputs=inputs,
                response_log=response_log,
                route_name="heungkuk_life_pipeline",
            )
        else:
            status_code, inference_results, response_log = pipeline.heungkuk_life(
                client=client, 
                inputs=inputs,
                response_log=response_log,
                route_name="heungkuk_life_pipeline",
            )
        
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            return set_json_response(code="3000", message="모델 서버 문제 발생")

        logger.debug(f'{task_id}-inference results:\n{inference_results}')

        kv_inference_results = inference_results.get('kv_detection_result')
        general_detection_result = inference_results.get('general_detection_result')
        classification_result = inference_results.get('classification_result')
        recognition_result = inference_results.get('recognition_result')
        
        logger.info(f'{task_id}-kv inference results:\n{pretty_dict(kv_inference_results)}')
        logger.info(f'{task_id}-classification inference results:\n{pretty_dict(classification_result)}')

        pp_inference_results = dict(
            boxes=kv_inference_results.get('boxes'),
            scores=kv_inference_results.get('scores'),
            classes=kv_inference_results.get("classes"),
            texts=kv_inference_results.get("texts"),
            id_type=inference_results.get("id_type"),
            doc_type=inference_results.get("doc_type"),
            image_height=inference_results.get("image_height"),
            image_width=inference_results.get("image_width"),
            task_id=task_id
        )


        # ocr post processing
        if settings.DEVELOP:
            if inputs.get("test_class", None) is not None:
                inference_results["doc_type"] = inputs.get("test_class")
                logger.debug(f'{task_id}-set test class: origin={inference_results.get("doc_type")}\
                     test_class={inputs.get("test_class")}')
        post_processing_type = get_pp_api_name(inference_results.get("doc_type"))
        logger.info(f'{task_id}-pp type:{post_processing_type}')
        if post_processing_type is not None and len(recognition_result["rec_preds"]) > 0:
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client, 
                request_id=request_id,
                response_log=response_log, 
                inference_results=pp_inference_results, 
                post_processing_type=post_processing_type, 
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="pp 과정에서 문제 발생")
            kv_inference_results["kv"] = post_processing_results["result"]
            kv_inference_results["texts"] = post_processing_results["texts"]

        if kv_inference_results.get("kv", None):
            logger.info(f'{task_id}-post-processed kv result:\n{pretty_dict(kv_inference_results.get("kv", {}))}')
            logger.info(f'{task_id}-post-processed text result:\n{pretty_dict(kv_inference_results.get("texts", {}))}')

        # convert preds to texts
        if convert_preds_to_texts is not None and "texts" not in kv_inference_results:
            status_code, texts = pp.convert_preds_to_texts(
                client=client, 
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            kv_inference_results["texts"] = texts

        # key-value model을 안타는 doc_type
        if not "kv" in kv_inference_results:
            kv_inference_results["kv"] = dict()
    
        dump_inference_results = dict(
            general_detection_result=general_detection_result,
            kv_detection_result=kv_inference_results.get("kv", {}),
            recognition_result=recognition_result,
            classification_result=classification_result
        )

        dump_inference_results["kv_detection_result"].update(dict(
            response_log=kv_inference_results.get("response_log")
        ))

        inference_results = set_ocr_response(**dump_inference_results)
        
        # background_tasks.add_task(
        #     func=save_updated_task,
        #     db=db,
        #     doc_type=inference_results.get("doc_type"),
        #     task_pkey=task_pkey
        # )
        
        # background_tasks.add_task(
        #     func=save_inference_results,
        #     db=db,
        #     inference_id=request_id,
        #     task_pkey=task_pkey,
        #     inference_img_path=inputs.get('image_path'),
        #     inference_results=dump_inference_results 
        # )

    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logging_response = dict(
        predictions=inference_results.get('predictions'),
        class_score=inference_results.get('class_score'),
        image_height=inference_results.get("image_height"),
        image_width=inference_results.get("image_width"),
        id_type=inference_results.get("id_type"),
        doc_type=inference_results.get('doc_type'),
    )

    logger.info(f'{task_id}-output:\n{pretty_dict(logging_response)}')
    logger.info(
        f"OCR api total time: \t{datetime.now() - start_time}"
    )
    return JSONResponse(content=jsonable_encoder(response))
