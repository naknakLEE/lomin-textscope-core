from copy import copy, deepcopy
import uuid
from app.utils.image import get_image_bytes

from httpx import Client

from typing import Any, Dict, Tuple, TypeVar
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.utils import get_pp_api_name, set_json_response, get_ts_uuid
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app.schemas.json_schema import inference_responses
from app.models import UserInfo as UserInfoInModel
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict
from app.utils.logging import logger
from app.utils.inference import get_removed_text_inference_result
from app.wrapper import pp, pipeline, settings
from app.database import query, schema
from app.database.connection import db
from app.schemas import error_models as ErrorResponse
from app.errors import exceptions as ex
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()

Pipeline = TypeVar("Pipeline")
PIPELINE_GOCR = pipeline.gocr_
PIPELINE_CLS = pipeline.cls_
PIPELINE_KV = pipeline.kv_
PIPELINE_IDCARD = pipeline.idcard_

INFERENCE_PIPELINE: Dict[str, Tuple[str, Pipeline]] = {
    "gocr":   [ ("gocr", PIPELINE_GOCR), ],
    "cls":    [ ("gocr", PIPELINE_GOCR), ("cls", PIPELINE_CLS) ],
    "kv":     [ ("gocr", PIPELINE_GOCR),                        ("kv", PIPELINE_KV) ],
    "cls-kv": [ ("gocr", PIPELINE_GOCR), ("cls", PIPELINE_CLS), ("kv", PIPELINE_KV) ],
    
    "idcard": [ ("idcard", PIPELINE_IDCARD) ]
}


@router.post("/ocr", status_code=200, responses=inference_responses)
def ocr(
    *,
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    x_request_id = inputs.get("x-request-id")
    logger.info(f"x-request-id : {x_request_id} / CORE - ocr START")
    
    start_time = datetime.now()
    response_log: Dict = dict()
    user_email = current_user.email
    log_id = inputs.get("log_id", get_ts_uuid("log"))
    document_id = inputs.get("document_id")
    document_path = inputs.get("document_path")
    target_page = inputs.get("page", 1)
    
    
    # parameter mapping:
    # web -> inference
    #   docx -> image
    # web -> pp
    #   log -> task
    task_id = log_id
    inputs["image_id"] = document_id
    inputs["image_path"] = document_path
    
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        logger.error(f"x-request-id : {x_request_id} / CORE - user validation error")
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team: str = select_user_result.user_team
    
    select_log_result = query.select_log(session, log_id=task_id) 
    if isinstance(select_log_result, schema.LogInfo):
        logger.error(f"x-request-id : {x_request_id} / CORE - log validation error")
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_log_result, JSONResponse):
        status_code_no_log, _ = ErrorResponse.ErrorCode.get(2201)
        if select_log_result.status_code != status_code_no_log:
            return select_log_result
    
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    insert_log_result = query.insert_log(
        session=session,
        log_id=task_id,
        user_email=user_email,
        user_team=user_team,
        log_content=dict({"request": inputs})
    )
    if isinstance(insert_log_result, JSONResponse):
        logger.error(f"x-request-id : {x_request_id} / CORE - log insert error")
        return insert_log_result
    
    # task_pkey = insert_task_result.task_pkey
    
    # text extraction from searchable pdf
    if Path(inputs.get("image_path", "")).suffix in [".pdf", ".PDF"] \
        and inputs.get("use_text_extraction"):
            
        parsed_text_info, image_size = get_pdf_text_info(inputs)
        if len(parsed_text_info) > 0:
            return JSONResponse(content=jsonable_encoder({
                "inference_results": parsed_text_info,
                "response_log": {"original_image_size": image_size},
            }))
    
    # get pipelines
    route_name = inputs.get("route_name", "gocr")
    inference_pipelines = INFERENCE_PIPELINE.get(route_name)
    
    # if cls-kv pipeline and hint.doc_type trust, use kv pipeline
    if route_name == "cls-kv":
        hint_doc_type: dict = inputs["kv"]["hint"]["doc_type"]
        if hint_doc_type["use"] and hint_doc_type["trust"]:
            inference_pipelines = INFERENCE_PIPELINE.get("kv")
    
    status_code, inference_results, response_log = (200, dict(), dict())
    with Client() as client:
        for (inference_name, inference_pipeline) in inference_pipelines:
            pipeline_start_time = datetime.now()
            response_log.update({f"inference_{inference_name}_start_time":pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
            
            status_code, inference_results, response_log = inference_pipeline(
                session,
                client,
                inputs,
                response_log,
                inference_result=inference_results
            )
            if isinstance(inference_results, JSONResponse):
                return inference_results
            
            pipeline_end_time = datetime.now()
            response_log.update({f"inference_{inference_name}_end_time":pipeline_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
            
            inference_total_start_time = response_log.get("inference_total_start_time", pipeline_start_time)
            response_log.update(
                inference_total_start_time=inference_total_start_time,
                inference_total_end_time=(inference_total_start_time - datetime.now()).total_seconds(),
            )
            logger.info("{} inference time: {}s", inference_name, (pipeline_end_time - pipeline_start_time).total_seconds())
    
    # DB에 저장하는 추론 결과에서 텍스트 또는 값 삭제 -> 개인정보 제거
    if hydra_cfg.database.delete_privacy_data:
        privacy_inference_results = get_removed_text_inference_result(inference_results)
    
    inference_id = get_ts_uuid("inference")
    insert_inference_result = query.insert_inference(
        session=session,
        inference_id=inference_id,
        document_id=document_id,
        user_email=user_email,
        user_team=user_team,
        inference_result=privacy_inference_results if hydra_cfg.database.delete_privacy_data else inference_results,
        inference_type=inputs.get("inference_type"),
        page_num=inference_results.get("page", target_page),
        doc_type_idx=inference_results.get("doc_type", {}).get("doc_type_idx", 0),
        response_log=response_log
    )
    if isinstance(insert_inference_result, JSONResponse):
        return insert_inference_result
    
    logger.info("OCR api : {}", (datetime.now() - start_time).total_seconds())
    
    
    response = dict(
        response_log=response_log,
        inference_results=inference_results,
        resource_id=dict(
            # log_id=task_id
        )
    )
    
    if inputs.get("background", False): return response
    
    return JSONResponse(content=jsonable_encoder(response))

# TODO: 토큰을 이용한 유저 체크 부분 활성화
@router.post("/ocr/old", status_code=200, responses=inference_responses)
def ocr_old(
    *,
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    cls-kv 적용전 ocr

    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    start_time = datetime.now()
    response_log: Dict = dict()
    user_email = current_user.email
    log_id = inputs.get("log_id", get_ts_uuid("log"))
    document_id = inputs.get("document_id")
    document_path = inputs.get("document_path")
    target_page = inputs.get("page", 1)
    
    
    # parameter mapping:
    # web -> inference
    #   docx -> image
    # web -> pp
    #   log -> task
    inputs["image_id"] = document_id
    inputs["image_path"] = document_path
    task_id = log_id
    
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team: str = select_user_result.user_team
    
    select_log_result = query.select_log(session, log_id=task_id) 
    if isinstance(select_log_result, schema.LogInfo):
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_log_result, JSONResponse):
        status_code_no_log, _ = ErrorResponse.ErrorCode.get(2201)
        if select_log_result.status_code != status_code_no_log:
            return select_log_result
    
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    insert_log_result = query.insert_log(
        session=session,
        log_id=task_id,
        user_email=user_email,
        user_team=user_team,
        log_content=dict({"request": inputs})
    )
    if isinstance(insert_log_result, JSONResponse):
        return insert_log_result
    
    # task_pkey = insert_task_result.task_pkey
    
    if (
        inputs.get("use_general_ocr")
        and Path(inputs.get("image_path", "")).suffix in [".pdf", ".PDF"]
        and inputs.get("use_text_extraction")
    ):
        parsed_text_info, image_size = get_pdf_text_info(inputs)
        if len(parsed_text_info) > 0:
            return JSONResponse(
                content=jsonable_encoder(
                    {
                        "inference_results": parsed_text_info,
                        "response_log": {"original_image_size": image_size},
                    }
                )
            )
    
    with Client() as client:        
        status_code, inference_results, response_log = pipeline.single(
            client=client,
            inputs=inputs,
            response_log=response_log,
            route_name=inputs.get("route_name", "ocr"),
            )

        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            status_code, error = ErrorResponse.ErrorCode.get(3501)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        
        # inference_result: response 생성에 필요한 값, inference_results: response 생성하기 위한 과정에서 생성된 inference 결과 포함한 값
        inference_result = inference_results
        if "kv_result" in inference_results:
            inference_result = inference_results.get("kv_result", {})
        logger.debug(f"{task_id}-inference results:\n{inference_results}")

        doc_type_code = inference_results.get("doc_type") if inference_results.get("doc_type") else inputs.get("doc_type")

        # KDT1-EST(TOCR)일 경우 kv에 바로 넣어주기 -> pp를 web을 통해 안보내므로
        if doc_type_code == 'KDT1-EST':
            inference_results['kv'] = inference_result.get('result')
        
        # convert preds to texts
        if (
            inputs.get("convert_preds_to_texts") is not None
            and "texts" not in inference_results
        ):
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3503)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            inference_results["texts"] = texts

        doc_type_code = inference_results.get("doc_type") if inputs.get("route_name") != "cls" else "cls"
        
        # Post processing
        # 한국평가데이터 cls일경우 kdt1_cls로 넘기기
        is_call_function = inputs.get('is_call_function', False)
        if(is_call_function):
            post_processing_type = None if inputs.get("route_name", None) == 'cls' else get_pp_api_name(doc_type_code)
        else:
            post_processing_type = 'kdt1_cls' if inputs.get("route_name", None) == 'cls' else get_pp_api_name(doc_type_code)

        if post_processing_type is not None \
            and doc_type_code is not None:        

            logger.info(f"{task_id}-pp type:{post_processing_type}")

            text_list = inference_result.get("texts", [])
            box_list = inference_result.get("boxes", [])
            score_list = inference_result.get("scores", [])
            class_list = inference_result.get("classes", [])
            
            score_list = score_list if len(score_list) > 0 else [ 0.0 for i in range(len(text_list)) ]
            class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]

            pp_inputs = dict(
                texts=text_list,
                boxes=box_list,
                scores=score_list,
                classes=class_list,
                rec_preds=inference_result.get("rec_preds"),
                id_type=inference_results.get("id_type"),
                doc_type=inference_results.get("doc_type"),
                image_height=inference_results.get("image_height"),
                image_width=inference_results.get("image_width"),
                relations=inference_results.get("relations"),
                cls_score=inference_result.get("cls_score"),
                task_id=task_id,
            )
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client,
                task_id=task_id,
                response_log=response_log,
                inputs=pp_inputs,
                post_processing_type=post_processing_type,
            )
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3502)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            
            if inputs.get("route_name") == 'cls':
                inference_results["doc_type"] = post_processing_results.get('result')['doc_type']
            else:
                inference_results["kv"] = post_processing_results.get("result") if post_processing_results.get("result") else {}
                
                logger.info(
                    f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
                )
            if "texts" not in inference_results:
                inference_results["texts"] = post_processing_results["texts"]
                logger.info(
                    f'{task_id}-post-processed text result:\n{pretty_dict(inference_results.get("texts", {}))}'
                )
            if post_processing_results.get('tables'):
                inference_results["tables"] = post_processing_results.get('tables')
                logger.info(
                    f'{task_id}-post-processed tables result:\n{pretty_dict(inference_results.get("tables", {}))}'
                )                
        
    
    response_log.update(inference_results.get("response_log", {}))
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")

    inference_id = get_ts_uuid("inference")
    # KDT1-EST(기업개요표 방어코드)    
    doc_type_code = inference_results.get("doc_type") if inference_results.get("doc_type") else doc_type_code
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_idx = select_doc_type_result.doc_type_idx
    inference_results.update(doc_type=dict(
        doc_type_idx=select_doc_type_result.doc_type_idx,
        doc_type_code=select_doc_type_result.doc_type_code,
        doc_type_code_parent=select_doc_type_result.doc_type_code_parent,
        doc_type_name_kr=select_doc_type_result.doc_type_name_kr,
        doc_type_name_en=select_doc_type_result.doc_type_name_en,
        doc_type_structed=select_doc_type_result.doc_type_structed
    ))

    # document.doc_type update - cls 일 경우만 분기
    if post_processing_type == "kbl1_cls":
        doc_type_idxs = []
        doc_type_codes = []
        doc_type_idxs.append(doc_type_idx)
        doc_type_codes.append(inference_result["kv"]["doc_type"])
        
        query.update_document(
            session, 
            document_id=document_id, 
            doc_type_idx=doc_type_idx,
            doc_type_idxs=doc_type_idxs,
            doc_type_codes=doc_type_codes
        )
    # 추론 결과에서 개인정보 삭제
    db_inference_results = get_removed_text_inference_result(deepcopy(inference_result), post_processing_type)
    insert_inference_result = query.insert_inference(
        session=session,
        inference_id=inference_id,
        document_id=document_id, 
        user_email=user_email,
        user_team=user_team,
        inference_result=db_inference_results,
        inference_type=inputs.get("inference_type"),
        page_num=inference_results.get("page", target_page),
        doc_type_idx=doc_type_idx,
        response_log=response_log
    )
    if isinstance(insert_inference_result, JSONResponse):
        return insert_inference_result
    insert_inference_result: schema.InferenceInfo = insert_inference_result
    
    inference_results.update(doc_type=insert_inference_result.inference_result.get("doc_type", dict()))
    
    
    response = dict(
        response_log=response_log,
        inference_results=inference_results,
        resource_id=dict(
            # log_id=task_id
        )
    )
    
    if(is_call_function): return response

    return JSONResponse(content=jsonable_encoder(response))

