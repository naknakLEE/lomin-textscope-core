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

TOCR_TEMPLATES = {
    "KBL1-IC": {
        "template_json": settings.KBL1_IC_TEMPLATE_JSON,
        "template_images": {
            "0": {
                "image_id": "template",
                "image_path": "보험금청구서_template_1.png",
                "image_bytes": settings.KBL1_IC_TEMPLATE_IMAGE_BASE64
            }
        }
    },
    "KBL1-PIC": {
        "template_json": settings.KBL1_PIC_TEMPLATE_JSON,
        "template_images": {
            "0": {
                "image_id": "template_1",
                "image_path": "개인정보동의서_템플릿_1.png",
                "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P1_BASE64
            },
            "1": {
                "image_id": "template_2",
                "image_path": "개인정보동의서_템플릿_2.png",
                "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P2_BASE64
            },
            "2": {
                "image_id": "template_3",
                "image_path": "개인정보동의서_템플릿_3.png",
                "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P3_BASE64
            }
        }
    }
}


def __kv__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    infernece_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    kv_inputs = dict()
    kv_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            inputs.get("doc_type"),
        request_id=          infernece_result.get("request_id"),
        image_width=         infernece_result.get("image_width"),
        image_height=        infernece_result.get("image_height"),
        texts=               infernece_result.get("texts"),
        boxes=               infernece_result.get("boxes"),
        scores=              infernece_result.get("scores"),
        image_width_origin=  infernece_result.get("image_width_origin"),
        image_height_origin= infernece_result.get("image_height_origin"),
        angle=               infernece_result.get("angle")
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
    infernece_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    el_inputs = dict()
    el_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            inputs.get("doc_type"),
        request_id=          infernece_result.get("request_id"),
        image_width=         infernece_result.get("image_width"),
        image_height=        infernece_result.get("image_height"),
        texts=               infernece_result.get("texts"),
        boxes=               infernece_result.get("boxes"),
        scores=              infernece_result.get("scores"),
        image_width_origin=  infernece_result.get("image_width_origin"),
        image_height_origin= infernece_result.get("image_height_origin"),
        angle=               infernece_result.get("angle")
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
    infernece_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    
    # get pp route
    post_processing_type = get_pp_api_name(doc_type_code)
    if post_processing_type is None:
        return (200, infernece_result, response_log)
    
    # TODO define get_template() func
    template = TOCR_TEMPLATES.get(doc_type_code)
    
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
    infernece_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    task_id = inputs.get("task_id")
    
    # get pp route
    post_processing_type = get_pp_api_name(doc_type_code)
    if post_processing_type is None:
        return (200, infernece_result, response_log)

    text_list = infernece_result.get("texts")
    
    class_list = infernece_result.get("classes", [])
    class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]
    
    pp_inputs = dict(
        texts=        text_list,
        boxes=        infernece_result.get("boxes"),
        scores=       infernece_result.get("scores"),
        classes=      class_list,
        relations=    infernece_result.get("relations", {}),
        rec_preds=    infernece_result.get("rec_preds"),
        id_type=      infernece_result.get("id_type"),
        doc_type=     inputs.get("doc_type"),
        image_height= infernece_result.get("image_height"),
        image_width=  infernece_result.get("image_width"),
        cls_score=    infernece_result.get("cls_score"),
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


# lomin_doc_type에 따른 kv-pipeline 정의
# (({pipelines}], [doc_types]), ...)
KV_PIPELINE = (
    ( (("pp",__pp__), ),              ["GV-BC", "GV-CFR", "GV-ARR"]),
    ( (("kv",__kv__), ("pp",__pp__)), ["MD-MC", "MD-DN", "MD-COT", "MD-CMT", "MD-CAD", "MD-CS"]),
    ( (("el",__el__), ("pp",__pp__)), ["MD-PRS", "MD-MB", "MD-MED", "MD-CPE"]),
    ( (("tocr",__tocr__), ),          ["KBL1-IC", "KBL1-PIC"])
)


def gocr_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    infernece_result: dict = None # None: gocr is first of whole inference pipelines
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
    infernece_result: dict = dict() # before pipeline might be gocr
) -> Tuple[int, dict, dict]:
    
    inputs.update(
        request_id=          infernece_result.get("request_id"),
        image_width=         infernece_result.get("image_width"),
        image_height=        infernece_result.get("image_height"),
        texts=               infernece_result.get("texts"),
        boxes=               infernece_result.get("boxes"),
        scores=              infernece_result.get("scores"),
        image_width_origin=  infernece_result.get("image_width_origin"),
        image_height_origin= infernece_result.get("image_height_origin"),
        angle=               infernece_result.get("angle")
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
    infernece_result: dict = dict() # before pipeline is gocr or cls
) -> Tuple[int, dict, dict]:
    
    inputs.update(
        request_id=          infernece_result.get("request_id"),
        image_width=         infernece_result.get("image_width"),
        image_height=        infernece_result.get("image_height"),
        texts=               infernece_result.get("texts"),
        boxes=               infernece_result.get("boxes"),
        scores=              infernece_result.get("scores"),
        image_width_origin=  infernece_result.get("image_width_origin"),
        image_height_origin= infernece_result.get("image_height_origin"),
        angle=               infernece_result.get("angle")
    )
    
    # if before pipeline was cls, can get cls_result from inference_result
    cls_result = dict(
        doc_type= infernece_result.get("doc_type", {}).get("doc_type_code", "None"),
        score=    infernece_result.get("cls_score", 1.0)
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
        return (status_code, infernece_result, response_log)
    
    for name, kv_pipline in kv_pipelines:
        pipeline_start_time = datetime.now()
        response_log.update({f"kv_{name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        status_code, infernece_result, response_log = kv_pipline(
            client,
            inputs,
            response_log,
            infernece_result=infernece_result
        )
        if isinstance(infernece_result, JSONResponse):
            return infernece_result
        
        pipeline_end_time = datetime.now()
        response_log.update({f"kv_{name}_end_time":pipeline_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        inference_total_start_time = response_log.get("kv_total_start_time", pipeline_start_time)
        response_log.update(
            inference_total_start_time=inference_total_start_time,
            inference_total_end_time=(inference_total_start_time - datetime.now()).total_seconds(),
        )
        logger.info("kv_pipeline {} time: {}s", name, (pipeline_end_time - pipeline_start_time).total_seconds())
    
    infernece_result.update(kv=infernece_result.pop("result"))
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    
    infernece_result.update(doc_type=dict(
        doc_type_idx=select_doc_type_result.doc_type_idx,
        doc_type_code=select_doc_type_result.doc_type_code,
        doc_type_code_parent=select_doc_type_result.doc_type_code_parent,
        doc_type_name_kr=select_doc_type_result.doc_type_name_kr,
        doc_type_name_en=select_doc_type_result.doc_type_name_en,
        doc_type_structed=select_doc_type_result.doc_type_structed
    ))
    
    
    return (status_code, infernece_result, response_log)
