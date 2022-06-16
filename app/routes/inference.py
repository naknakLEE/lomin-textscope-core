import uuid

from httpx import Client

from typing import Dict
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.utils import get_pp_api_name, set_json_response
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app.schemas.json_schema import inference_responses
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict
from app.utils.logging import logger
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


# TODO: 토큰을 이용한 유저 체크 부분 활성화
@router.post("/ocr", status_code=200, responses=inference_responses)
def ocr(
    *,
    inputs: Dict = Body(...),
    current_user: dict = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    start_time = datetime.now()
    response_log: Dict = dict()
    response: Dict = dict()
    task_id = inputs.get("task_id")
    document_id = inputs.get("document_id")
    document_path = inputs.get("document_path")
    target_page = inputs.get("page", 1)
    user_email = inputs.get("user_email", "do@not.use")
    
    # parameter mapping: web -> inference
    inputs["image_id"] = document_id
    inputs["image_path"] = document_path
    
    select_user_result = query.select_user(session, user_email=user_email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    
    user_team: str = select_user_result.user_team
    
    select_task_result = query.select_task(session, task_id=task_id) 
    if isinstance(select_task_result, schema.TaskInfo):
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_task_result, JSONResponse):
        status_code_no_task, _ = ErrorResponse.ErrorCode.get(2201)
        if select_task_result.status_code != status_code_no_task:
            return select_task_result
    
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    insert_task_result = query.insert_task(
        session=session,
        task_id=task_id,
        user_email=user_email,
        user_team=user_team,
        task_content=dict({"request": inputs})
    )
    if isinstance(insert_task_result, JSONResponse):
        return insert_task_result
    
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
        # Inference
        if settings.USE_OCR_PIPELINE == 'multiple':
            # TODO: sequence_type을 wrapper에서 받도록 수정
            # TODO: python 3.6 버전에서 async profiling 사용에 제한이 있어 sync로 변경했는데 추후 async 사용해 micro bacing 사용하기 위해서는 다시 변경 필요
            status_code, inference_results, response_log = pipeline.multiple(
                client=client,
                inputs=inputs,
                sequence_type="kv",
                response_log=response_log,
            )
            response_log = dict()
        elif settings.USE_OCR_PIPELINE == 'duriel':
            status_code, inference_results, response_log = pipeline.heungkuk_life(
                client=client,
                inputs=inputs,
                response_log=response_log,
                route_name=inputs.get("route_name", "ocr"),
            )
        elif settings.USE_OCR_PIPELINE == 'single':
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
        
        
        # Post processing
        post_processing_type = get_pp_api_name(inference_results.get("doc_type", ""))
        logger.info(f"{task_id}-pp type:{post_processing_type}")
        if (
            post_processing_type is not None
        ):
            pp_inputs = dict(
                boxes=inference_result.get("boxes"),
                scores=inference_result.get("scores"),
                classes=inference_result.get("classes"),
                rec_preds=inference_result.get("rec_preds"),
                texts=inference_results.get("texts"),
                id_type=inference_results.get("id_type"),
                doc_type=inference_results.get("doc_type"),
                image_height=inference_results.get("image_height"),
                image_width=inference_results.get("image_width"),
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
            inference_results["kv"] = post_processing_results["result"]
            logger.info(
                f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
            )
            if "texts" not in inference_results:
                inference_results["texts"] = post_processing_results["texts"]
                logger.info(
                    f'{task_id}-post-processed text result:\n{pretty_dict(inference_results.get("texts", {}))}'
                )
        
    
    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")
    
    inference_id = str(uuid.uuid4())
    insert_inference_result = query.insert_inference(
        session=session,
        inference_id=inference_id,
        document_id=document_id,
        user_email=user_email,
        user_team=user_team,
        model_index=0,
        inference_result=inference_results,
        inference_type=inputs.get("inference_type"),
        page_num=inference_results.get("page", target_page),
        response_log=response_log
    )
    if isinstance(insert_inference_result, JSONResponse):
        return insert_inference_result
    
    return JSONResponse(content=jsonable_encoder(response))
