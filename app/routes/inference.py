from httpx import Client

from typing import Dict
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.auth import get_current_active_user
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
from app.database import query
from app.database.connection import db


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
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")

    task_pkey = query.insert_task(
        session, task_id, inputs.get("image_pkey", ""), auto_commit=False
    )

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
        else:
            status_code, inference_results, response_log = pipeline.single(
                client=client,
                inputs=inputs,
                response_log=response_log,
                route_name=inputs.get("route_name", "ocr"),
            )
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            return set_json_response(code="3000", message="모델 서버 문제 발생")

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
            and len(inference_results.get("rec_preds", [])) > 0
        ):
            pp_inputs = dict(
                boxes=inference_result.get("boxes"),
                scores=inference_result.get("scores"),
                classes=inference_result.get("classes"),
                rec_preds=inference_result.get("rec_preds"),
                texts=inference_result.get("texts"),
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
                return set_json_response(code="3000", message="pp 과정에서 문제 발생")
            inference_results["kv"] = post_processing_results["result"]
            logger.info(
                f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
            )
            if "texts" not in inference_results:
                inference_results["texts"] = post_processing_results["texts"]
                logger.info(
                    f'{task_id}-post-processed text result:\n{pretty_dict(inference_results.get("texts", {}))}'
                )

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
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            inference_results["texts"] = texts

    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")

    # TODO: 각 모델마다 결과 저장하도록 구성
    if settings.DEVELOP:
        background_tasks.add_task(
            func=query.insert_inference_result,
            session=session,
            task_pkey=task_pkey,
            image_pkey=inputs.get("image_pkey"),
            inference_type=inputs.get("inference_type"),
            response_log=response_log,
            inference_results=inference_results,
        )
    return JSONResponse(content=jsonable_encoder(response))
