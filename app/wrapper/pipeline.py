import base64
import json
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from httpx import Client

from sqlalchemy.orm import Session

from app.common import settings
from app.database import query, schema
from app.models import DocTypeHint
from app.utils.hint import apply_cls_hint
from app.utils.logging import logger
from app.utils.utils import get_pp_api_name
from app.schemas import error_models as ErrorResponse

model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
pp_server_url = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


def __kv__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    kv_inputs = dict()
    kv_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            inputs.get("doc_type"),
        request_id=          inference_result.get("request_id"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        texts=               inference_result.get("texts"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
        angle=               inference_result.get("angle")
    )
    
    # kv inference 요청
    kv_response = client.post(
        f"{model_server_url}/kv",
        json=kv_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    
    return (kv_response.status_code, kv_response.json(), response_log)


def __el__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    el_inputs = dict()
    el_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            inputs.get("doc_type"),
        request_id=          inference_result.get("request_id"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        texts=               inference_result.get("texts"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
        angle=               inference_result.get("angle")
    )
    
    # el inference 요청
    el_response = client.post(
        f"{model_server_url}/el",
        json=el_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    
    return (el_response.status_code, el_response.json(), response_log)


def __tocr__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    
    # get pp route
    post_processing_type = get_pp_api_name(doc_type_code)
    if post_processing_type is None:
        return (200, inference_result, response_log)
    
    # TODO define get_template() func
    template = settings.TOCR_TEMPLATES.get(doc_type_code)
    
    tocr_inputs = dict()
    tocr_inputs.update(
        image_id=     inputs.get("image_id"),
        image_path=   inputs.get("image_path"),
        doc_type=     doc_type_code,
        pp_end_point= post_processing_type,
        template=     template
    )
    
    # tocr inference 요청
    tocr_response = client.post(
        f"{model_server_url}/tocr",
        json=tocr_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    
    return (tocr_response.status_code, tocr_response.json(), response_log)


def __pp__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    task_id = inputs.get("task_id")
    
    # get pp route
    post_processing_type = get_pp_api_name(doc_type_code)
    if post_processing_type is None:
        return (200, inference_result, response_log)

    text_list = inference_result.get("texts")
    
    class_list = inference_result.get("classes", [])
    class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]
    
    pp_inputs = dict(
        texts=        text_list,
        boxes=        inference_result.get("boxes"),
        scores=       inference_result.get("scores"),
        classes=      class_list,
        relations=    inference_result.get("relations", {}),
        rec_preds=    inference_result.get("rec_preds"),
        id_type=      inference_result.get("id_type"),
        doc_type=     doc_type_code,
        image_height= inference_result.get("image_height"),
        image_width=  inference_result.get("image_width"),
        cls_score=    inference_result.get("cls_score"),
        task_id=      task_id,
    )
    pp_response = client.post(
        f"{pp_server_url}/post_processing/{post_processing_type}",
        json=pp_inputs,
        timeout=settings.TIMEOUT_SECOND,
    )
    
    pp_response_json: dict = pp_response.json()
    
    status_code = pp_response.status_code
    if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
        status_code, error = ErrorResponse.ErrorCode.get(3502)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    
    return (pp_response, pp_response_json, response_log)


def __idcard__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: __idcard__ is first of whole idcard pipelines
) -> Tuple[int, dict, dict]:
    
    # idcard inference 요청
    idcard_response = client.post(
        f"{model_server_url}/idcard",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    idcard_response_json: dict = idcard_response.json()
    
    # get real doc_type_code from classes
    doc_type_code = "-".join(idcard_response_json.get("classes", [])[0].split("-")[:2])
    
    inputs.update(doc_type=doc_type_code)
    idcard_response_json.update(doc_type=doc_type_code)
    
    
    return (idcard_response.status_code, idcard_response_json, response_log)


# lomin_doc_type에 따른 kv-pipeline 정의
# assets/bsn/{bsn_code}.json에 따라 수정하기 쉽게 변경 필요
# (({pipelines}], [doc_types]), ...)
KV_PIPELINE = (
    ( (("pp",__pp__), ),              ["GOCR"]),
    ( (("kv",__kv__), ("pp",__pp__)), [ ]),
    ( (("el",__el__), ("pp",__pp__)), [ ]),
    ( (("tocr",__tocr__), ),          [ ]),
    
    ( (("idcard",__idcard__), ("pp",__pp__)), ["ID-RRC", "ID-DLC", "ID-ARC", "ID-PP"])
)


def rotate_(
    client: Client,
    inputs: dict,
    response_log: dict = {},
) -> Tuple[int, dict, dict]:
    
    rotate_response = client.post(
        f"{model_server_url}/rotate",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    status_code = rotate_response.status_code
    if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
        status_code, error = ErrorResponse.ErrorCode.get(3500)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    
    return (status_code, rotate_response.json(), response_log)

def gocr_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: gocr is first of whole inference pipelines
) -> Tuple[int, dict, dict]:
    
    gocr_response = client.post(
        f"{model_server_url}/gocr",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    status_code = gocr_response.status_code
    if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
        status_code, error = ErrorResponse.ErrorCode.get(3501)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    
    return (status_code, gocr_response.json(), response_log)


def cls_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict() # before pipeline might be gocr
) -> Tuple[int, dict, dict]:
    
    inputs.update(
        request_id=          inference_result.get("request_id"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        texts=               inference_result.get("texts"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
        angle=               inference_result.get("angle")
    )
    
    cls_response = client.post(
        f"{model_server_url}/cls",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    status_code = cls_response.status_code
    if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
        status_code, error = ErrorResponse.ErrorCode.get(3501)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    cls_response_json: dict = cls_response.json()
    
    # doc_type_code로 doc_type_index 조회
    doc_type_code = cls_response_json.get("doc_type")
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    
    cls_response_json.update(doc_type=dict(
        doc_type_idx=select_doc_type_result.doc_type_idx,
        doc_type_code=select_doc_type_result.doc_type_code,
        doc_type_code_parent=select_doc_type_result.doc_type_code_parent,
        doc_type_name_kr=select_doc_type_result.doc_type_name_kr,
        doc_type_name_en=select_doc_type_result.doc_type_name_en,
        doc_type_structed=select_doc_type_result.doc_type_structed
    ))
    
    
    return (status_code, cls_response_json, response_log)


def kv_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict() # before pipeline is gocr or cls
) -> Tuple[int, dict, dict]:
    
    inputs.update(
        request_id=          inference_result.get("request_id"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        texts=               inference_result.get("texts"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
        angle=               inference_result.get("angle")
    )
    
    # if before pipeline was cls, can get cls_result from inference_result
    cls_result = dict(
        # doc_type= inference_result.get("doc_type", {}).get("doc_type_code", "None"),
        doc_type= inference_result.get("doc_type", {}).get("doc_type_code", "GOCR"),
        score=    inference_result.get("cls_score", 1.0)
    )
    
    # Apply doc type hint
    hint = inputs.get("kv", {}).get("hint", {})
    if hint is not None and hint.get("doc_type") is not None:
        doc_type_hint = hint.get("doc_type", {})
        doc_type_hint = DocTypeHint(**doc_type_hint)
        cls_hint_result = apply_cls_hint(
            doc_type_hint=doc_type_hint,
            cls_result=cls_result
        )
        response_log.update(apply_cls_hint_result=cls_hint_result)
        inputs.update(
            doc_type=cls_hint_result.get("doc_type")
        )
    
    # 여기서 doc_type_code에 따라 kv-pp, el-pp, tocr-pp, pp로 나누기
    doc_type_code = inputs.get("doc_type")
    
    kv_pipelines = ()
    for pipelines, doc_type_codes in KV_PIPELINE:
        if doc_type_code in doc_type_codes:
            kv_pipelines = pipelines
            break
    
    logger.info("kv pipeline: {}", [ p for p, _ in kv_pipelines ] )
    
    status_code, response_log = (200, dict())
    
    # was only cls
    if len(kv_pipelines) == 0:
        return (status_code, inference_result, response_log)
    
    for name, kv_pipline in kv_pipelines:
        pipeline_start_time = datetime.now()
        response_log.update({f"kv_{name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        kv_pipeline_result = kv_pipline(
            client,
            inputs,
            response_log,
            inference_result=inference_result
        )
        if isinstance(kv_pipeline_result, JSONResponse):
            return kv_pipeline_result
        
        status_code, inference_result, response_log = kv_pipeline_result
        
        pipeline_end_time = datetime.now()
        response_log.update({f"kv_{name}_end_time":pipeline_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        inference_total_start_time = response_log.get("kv_total_start_time", pipeline_start_time)
        response_log.update(
            inference_total_start_time=inference_total_start_time,
            inference_total_end_time=(inference_total_start_time - datetime.now()).total_seconds(),
        )
        logger.info("kv_pipeline {} time: {}s", name, (pipeline_end_time - pipeline_start_time).total_seconds())
    
    inference_result.update(kv=inference_result.pop("result"))
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    
    inference_result.update(doc_type=dict(
        doc_type_idx=select_doc_type_result.doc_type_idx,
        doc_type_code=select_doc_type_result.doc_type_code,
        doc_type_code_parent=select_doc_type_result.doc_type_code_parent,
        doc_type_name_kr=select_doc_type_result.doc_type_name_kr,
        doc_type_name_en=select_doc_type_result.doc_type_name_en,
        doc_type_structed=select_doc_type_result.doc_type_structed
    ))
    
    
    return (status_code, inference_result, response_log)


def idcard_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: idcard use own det, rec models
) -> Tuple[int, dict, dict]:
    
    idcard_pipelines = KV_PIPELINE[4][0]
    
    logger.info("idcard pipeline: {}", [ p for p, _ in idcard_pipelines ] )
    
    status_code, response_log = (200, dict())
    
    for name, idcard_pipeline in idcard_pipelines:
        pipeline_start_time = datetime.now()
        response_log.update({f"kv_{name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        status_code, inference_result, response_log = idcard_pipeline(
            client,
            inputs,
            response_log,
            inference_result=inference_result
        )
        if isinstance(inference_result, JSONResponse):
            return inference_result
        
        pipeline_end_time = datetime.now()
        response_log.update({f"kv_{name}_end_time":pipeline_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        inference_total_start_time = response_log.get("kv_total_start_time", pipeline_start_time)
        response_log.update(
            inference_total_start_time=inference_total_start_time,
            inference_total_end_time=(inference_total_start_time - datetime.now()).total_seconds(),
        )
        logger.info("idcard_pipeline {} time: {}s", name, (pipeline_end_time - pipeline_start_time).total_seconds())
    
    inference_result.update(kv=inference_result.pop("result"))
    
    doc_type_code = inputs.get("doc_type")
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    
    inference_result.update(doc_type=dict(
        doc_type_idx=select_doc_type_result.doc_type_idx,
        doc_type_code=select_doc_type_result.doc_type_code,
        doc_type_code_parent=select_doc_type_result.doc_type_code_parent,
        doc_type_name_kr=select_doc_type_result.doc_type_name_kr,
        doc_type_name_en=select_doc_type_result.doc_type_name_en,
        doc_type_structed=select_doc_type_result.doc_type_structed
    ))
    
    
    return (status_code, inference_result, response_log)
