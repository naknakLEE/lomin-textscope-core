from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from httpx import Client

from sqlalchemy.orm import Session

from app.common.const import settings
from app.database import query, schema
from app.models import DocTypeHint
from app.utils.hint import apply_cls_hint
from app.utils.logging import logger
from app.utils.utils import get_pp_api_name
from app.schemas import error_models as ErrorResponse

pp_server_url = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"
SERVING_MAPPING: dict =     settings.BSN_CONFIG.get("SERVING_MAPPING_TABLE")
KV_PIPELINE_MAPPING: dict = settings.BSN_CONFIG.get("KV_PIPELINE_MAPPING_TABLE")
TOCR_TEMPLATES: dict =      settings.BSN_CONFIG.get("TOCR_TEMPLATES")


def _get_serving_host(pipeline_name: str, doc_type_code: str):
    
    default_host = SERVING_MAPPING.get("DEFAULT", "http://textscope-serving:5000")
    host_info = SERVING_MAPPING.get(pipeline_name, default_host)
    
    # 간단 방식
    if isinstance(host_info, str):
        return host_info
    
    # 상세 정보
    for doc_type_host in host_info:
        if doc_type_code in doc_type_host["doc_type"]:
            host = doc_type_host["host"]
            break
    
    
    return host


def __kv__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    
    kv_inputs = dict()
    kv_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            doc_type_code,
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
        f'{_get_serving_host("kv", doc_type_code)}/kv',
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
    
    doc_type_code = inputs.get("doc_type")
    
    el_inputs = dict()
    el_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            doc_type_code,
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
        f'{_get_serving_host("el", doc_type_code)}/el',
        json=el_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    
    return (el_response.status_code, el_response.json(), response_log)


def __kvel__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = dict()
) -> Tuple[int, dict, dict]:
    
    doc_type_code = inputs.get("doc_type")
    
    kvel_inputs = dict()
    kvel_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            doc_type_code,
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
        f'{_get_serving_host("kvel", doc_type_code)}/kvel',
        json=kvel_inputs,
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
    pp_api_list = get_pp_api_name(doc_type_code)
    logger.info("tocr pp api : {}", pp_api_list[0])
    
    # pp_api_list is defined with no api
    if len(pp_api_list) == 0:
        return (200, inference_result, response_log)
    
    # TODO define get_template() func
    template = TOCR_TEMPLATES.get(doc_type_code)
    
    tocr_inputs = dict()
    tocr_inputs.update(
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        doc_type=            doc_type_code,
        request_id=          inference_result.get("request_id"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        texts=               inference_result.get("texts"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
        angle=               inference_result.get("angle"),
        pp_end_point=        pp_api_list[0],
        template=            template
    )
    
    # tocr inference 요청
    tocr_response = client.post(
        f'{SERVING_MAPPING.get("tocr")}/tocr',
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
    pp_api_list = get_pp_api_name(doc_type_code)
    logger.info("pp api list: {}", pp_api_list)
    
    # pp_api_list is defined with no api
    if len(pp_api_list) == 0:
        return (200, inference_result, response_log)
    
    text_list = inference_result.get("texts", [])
    
    class_list = inference_result.get("classes", [])
    class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]
    
    pp_inputs = dict(
        texts=        text_list,
        boxes=        inference_result.get("boxes"),
        scores=       inference_result.get("scores"),
        classes=      class_list,
        all_boxes_x=  inference_result.get("all_boxes_x"),
        all_boxes_y=  inference_result.get("all_boxes_y"),
        texts_wraped= inference_result.get("texts_wraped"),
        boxes_wraped= inference_result.get("boxes_wraped"),
        scores_wraped=inference_result.get("scores_wraped"),
        classes_wraped=inference_result.get("classes_wraped"),
        result=       inference_result.get("result"),
        relations=    inference_result.get("relations"),
        tables=       inference_result.get("tables"),
        rec_preds=    inference_result.get("rec_preds"),
        id_type=      inference_result.get("id_type"),
        doc_type=     doc_type_code,
        image_height= inference_result.get("image_height"),
        image_width=  inference_result.get("image_width"),
        cls_score=    inference_result.get("cls_score"),
        task_id=      task_id,
    )
    
    pp_response_json = dict()
    for pp_api in pp_api_list:
        pp_response = client.post(
            f"{pp_server_url}/post_processing/{pp_api}",
            json=pp_inputs,
            timeout=settings.TIMEOUT_SECOND,
        )
        
        pp_inputs.update(pp_response.json())
        
        # pp_response_json.result에 결과를 넣어주는 pp api가 있어서 로직 추가
        pp_response_json_result = pp_inputs.get("result", {})
        if pp_response_json_result.get("doc_type"):
            pp_inputs.update(doc_type=pp_response_json_result.pop("doc_type", "ETC"))
        
        if pp_response_json_result.get("cls_score"):
            pp_inputs.update(cls_score=pp_response_json_result.pop("cls_score", 0.0))
    
    pp_response_json: dict = pp_inputs
    
    status_code = pp_response.status_code
    if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
        status_code, error = ErrorResponse.ErrorCode.get(3502)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
    doc_type_code = pp_inputs.get("doc_type", "ETC")
    
    
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
        f'{SERVING_MAPPING.get("idcard")}/idcard',
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    idcard_response_json: dict = idcard_response.json()
    
    return (idcard_response.status_code, idcard_response_json, response_log)


def __idcard_kp__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: __idcard_kp__ is first of whole idcard pipelines
) -> Tuple[int, dict, dict]:
    
    # idcard inference 요청
    idcard_kp_response = client.post(
        f'{SERVING_MAPPING.get("idcard_kp")}/idcard_kp',
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    idcard_kp_response_json: dict = idcard_kp_response.json()
    
    return (idcard_kp_response.status_code, idcard_kp_response_json, response_log)


def __cell_detect__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # before pipeline might be gocr
) -> Tuple[int, dict, dict]:
    
    inputs.update(
        request_id=          inference_result.get("request_id"),
        image_id=            inputs.get("image_id"),
        image_path=          inputs.get("image_path"),
        angle=               inference_result.get("angle"),
        texts=               inference_result.get("texts"),
        classes=             inference_result.get("classes"),
        boxes=               inference_result.get("boxes"),
        scores=              inference_result.get("scores"),
        image_width=         inference_result.get("image_width"),
        image_height=        inference_result.get("image_height"),
        image_width_origin=  inference_result.get("image_width_origin"),
        image_height_origin= inference_result.get("image_height_origin"),
    )
    
    cell_detect_response = client.post(
        f'{SERVING_MAPPING.get("cell_detection")}/cell_detection',
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    cell_detect_response_json: dict = cell_detect_response.json()
    
    
    return (cell_detect_response.status_code, cell_detect_response_json, response_log)


def __bankbook__(
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: __bankbook__ is first of whole idcard pipelines
) -> Tuple[int, dict, dict]:
    
    # bankbook inference 요청
    bankbook_response = client.post(
        f'{SERVING_MAPPING.get("bankbook")}/bankbook',
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    bankbook_response_json: dict = bankbook_response.json()
    
    return (bankbook_response.status_code, bankbook_response_json, response_log)


# lomin_doc_type에 따른 kv-pipeline 정의
# ( [doc_types], ([{pipelines}]) )
KV_PIPELINE = (
    ( KV_PIPELINE_MAPPING.get("pp", []),          (("pp",__pp__), ) ),
    ( KV_PIPELINE_MAPPING.get("kv", []),          (("kv",__kv__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("el", []),          (("el",__el__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("kvel", []),        (("kvel",__kvel__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("tocr", []),        (("tocr",__tocr__), ) ),
    
    ( KV_PIPELINE_MAPPING.get("idcard", []),      (("idcard",__idcard__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("idcard_kp", []),   (("idcard_kp",__idcard_kp__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("cell_detect", []), (("cell_detect",__cell_detect__), ("pp",__pp__)) ),
    ( KV_PIPELINE_MAPPING.get("bankbook", []),    (("bankbook",__bankbook__), ("pp",__pp__)) ),
)

def _get_kv_pipelines(doc_type_code: str):
    
    kv_pipelines = []
    for doc_type_codes, pipelines in KV_PIPELINE:
        if doc_type_code in doc_type_codes:
            kv_pipelines = pipelines
            break
    
    
    return kv_pipelines


def rotate_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: only rotate
) -> Tuple[int, dict, dict]:
    
    rotate_response = client.post(
        f'{SERVING_MAPPING.get("rotate")}/rotate',
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
        f'{SERVING_MAPPING.get("gocr")}/gocr',
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
        f'{SERVING_MAPPING.get("cls")}/cls',
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
        doc_type= inference_result.get("doc_type", {}).get("doc_type_code", "None"),
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
    
    kv_pipelines = _get_kv_pipelines(doc_type_code)
    logger.info("kv pipeline: {}", [ p for p, _ in kv_pipelines ] )
    
    # was only cls
    if len(kv_pipelines) == 0:
        return (200, inference_result, response_log)
    
    for name, kv_pipeline in kv_pipelines:
        pipeline_start_time = datetime.now()
        response_log.update({f"kv_{name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        kv_pipeline_result = kv_pipeline(
            client,
            inputs,
            response_log,
            inference_result=inference_result
        )
        if isinstance(kv_pipeline_result, JSONResponse):
            return inference_result
        
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

    # ID-RRC는 idcard의 대표 서식코드
    doc_type_code = "ID-RRC"
    inputs["doc_type"] = doc_type_code
    
    idcard_pipelines = _get_kv_pipelines(doc_type_code)
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
    
    doc_type_code = inference_result.get("doc_type", "ETC")

    if doc_type_code == '':
        inference_result = {}
    else:
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


def bankbook_(
    session: Session,
    client: Client,
    inputs: dict,
    response_log: dict,
    /,
    inference_result: dict = None # None: bankbook use own det, rec models
) -> Tuple[int, dict, dict]:
    
    doc_type_code = "bankbook"
    inputs["doc_type"] = doc_type_code
    
    bankbook_pipelines = _get_kv_pipelines(doc_type_code)
    logger.info("bankbook pipeline: {}", [ p for p, _ in bankbook_pipelines ] )
    
    status_code, response_log = (200, dict())
    
    for name, bankbook_pipeline in bankbook_pipelines:
        pipeline_start_time = datetime.now()
        response_log.update({f"kv_{name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        
        status_code, inference_result, response_log = bankbook_pipeline(
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
        logger.info("bankbook_pipeline {} time: {}s", name, (pipeline_end_time - pipeline_start_time).total_seconds())
    
    inference_result.update(kv=inference_result.pop("result"))
    
    doc_type_code = "FN-BB"

    if doc_type_code == '':
        inference_result = {}
    else:
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
