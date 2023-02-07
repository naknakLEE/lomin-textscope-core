from httpx import Client, AsyncClient

from typing import Dict
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.auth import get_current_active_user
from app.utils.utils import get_pp_api_name, set_json_response
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app.utils.image import load_image
from app.schemas.json_schema import inference_responses
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict
from app.utils.logging import logger
from app.wrapper import pp, pipeline, settings
from app.database import query, schema
from app.database.connection import db
from app.schemas import error_models as ErrorResponse
from app.utils.postprocess import get_unmodified_bbox
from app.errors import exceptions as ex
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


# TODO: 토큰을 이용한 유저 체크 부분 활성화
@router.post("/ocr", status_code=200, responses=inference_responses)
async def ocr(
    *,
    inputs: Dict = Body(...),
    current_user: dict = Depends(get_current_active_user),
    session: Session = Depends(db.session),
    background_tasks: BackgroundTasks,
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    start_time = datetime.now()
    response_log: Dict = dict()
    response: Dict = dict()
    
    task_id = inputs.get("task_id", "")
    select_task_result = query.select_task(session, task_id=task_id)
    
    if isinstance(select_task_result, schema.Task):
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_task_result, JSONResponse):
        status_code_no_task, _ = ErrorResponse.ErrorCode.get(2201)
        if select_task_result.status_code != status_code_no_task:
            return select_task_result
    
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    insert_task_result = query.insert_task(
        session,
        task_id,
        inputs.get("image_pkey"), 
        "INFERENCE",
        auto_commit=True
    )
    if isinstance(insert_task_result, JSONResponse):
        return insert_task_result
    
    task_pkey = insert_task_result.task_pkey
    
    load_image_res = load_image(inputs)
    if load_image_res == None:
        status_code, error = ErrorResponse.ErrorCode.get(2105)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    
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
    
    
    async with AsyncClient() as client:
        status_code, inference_results, response_log = await pipeline.single(
            client=client,
            inputs=inputs,
            response_log=response_log,
            route_name=inputs.get("route_name", "gocr"),
        )
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            status_code, error = ErrorResponse.ErrorCode.get(3501)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))

        # convert preds to texts
        if (
            inputs.get("convert_preds_to_texts") is not None
            and "texts" not in inference_results
        ):
            status_code, texts = await pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3503)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            inference_results["texts"] = texts            
        
        # inference_result: response 생성에 필요한 값, inference_results: response 생성하기 위한 과정에서 생성된 inference 결과 포함한 값
        inference_result = inference_results
        if "kv_result" in inference_results:
            inference_result = inference_results.get("kv_result", {})
        logger.debug(f"{task_id}-inference results:\n{inference_results}")
                
        # Post processing
        post_processing_type = get_pp_api_name(inference_results.get("doc_type", ""))
        logger.info(f"{task_id}-pp type:{post_processing_type}")
        if (
            post_processing_type is not None
            and len(inference_results.get("texts", [])) > 0
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
                transform_matrix=inference_results.get("transform_matrix", []),
                angle=inference_results.get("angle", 0),
                task_id=task_id
            )
            if post_processing_type == 'general_idcard':    
                pp_inputs['all_boxes_x'] = inference_results.get("all_boxes_x")
                pp_inputs['all_boxes_y'] = inference_results.get("all_boxes_y")
                pp_inputs['texts_wraped'] = inference_results.get("texts_wraped")
                pp_inputs['scores_wraped'] = inference_results.get("scores_wraped")
                pp_inputs['boxes_wraped'] = inference_results.get("boxes_wraped")
                pp_inputs['classes_wraped'] = inference_results.get("classes_wraped")
            elif post_processing_type == 'bankbook':
                inference_results.update({
                    'doc_type': post_processing_type
                })
            status_code, post_processing_results, response_log = await pp.post_processing(
                client=client,
                task_id=task_id,
                response_log=response_log,
                inputs=pp_inputs,
                post_processing_type= "sgi_idcard" if post_processing_type == 'general_idcard' else post_processing_type,
            )

            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3502)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            # pp결과의 kv가 없을경우 빈 dict반환
            inference_results["kv"] = post_processing_results["result"] if post_processing_results["result"] is not None else []
            logger.info(
                f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
            )
            if "texts" not in inference_results:
                inference_results["texts"] = post_processing_results["texts"]
                logger.info(
                    f'{task_id}-post-processed text result:\n{pretty_dict(inference_results.get("texts", {}))}'
                )
        if(len(inference_results.get("texts", [])) > 0 and post_processing_type != 'general_idcard'):
            inference_results = get_unmodified_bbox(inference_results)
    inference_results.update(
        pp_doc_type=post_processing_results.get("doc_type") or inference_results.get("doc_type", "")
    )
    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")

    return JSONResponse(content=jsonable_encoder(response))
