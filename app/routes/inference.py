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
    
    logger.info("#0-1 inference start at {}", datetime.now())
    logger.info("#0-2 start document_id: {}", document_id)
    logger.info("#0-3 document_filename: {}", document_path.split("/")[-1])
    
    logger.info ("[{}] #1-1 try select user info from db", datetime.now())
    select_user_result = query.select_user(session, user_email=user_email)
    logger.info ("[{}] #1-2 end select user info from db (result: {})", datetime.now(), select_user_result)
    
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team: str = select_user_result.user_team
    
    logger.info ("[{}] #2-1 try select log info from db", datetime.now())
    select_log_result = query.select_log(session, log_id=task_id) 
    if isinstance(select_log_result, schema.LogInfo):
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_log_result, JSONResponse):
        status_code_no_log, _ = ErrorResponse.ErrorCode.get(2201)
        if select_log_result.status_code != status_code_no_log:
            return select_log_result
    logger.info ("[{}] #2-2 end select log info from db (result: {})", datetime.now(), select_log_result)
    
    # logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    logger.info ("[{}] #3-1 try insert log info to db", datetime.now())
    insert_log_result = query.insert_log(
        session=session,
        log_id=task_id,
        user_email=user_email,
        user_team=user_team,
        log_content=dict({"request": inputs})
    )
    logger.info ("[{}] #3-2 end insert log info to db (result: {})", datetime.now(), insert_log_result)
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
        # Inference
        logger.info ("[{}] #4-1 try inference pipline({})", datetime.now(), settings.USE_OCR_PIPELINE)
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
        logger.info ("[{}] #4-2 try inference pipline({}) (status code: {})", datetime.now(), settings.USE_OCR_PIPELINE, status_code)
        
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            status_code, error = ErrorResponse.ErrorCode.get(3501)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        
        # inference_result: response 생성에 필요한 값, inference_results: response 생성하기 위한 과정에서 생성된 inference 결과 포함한 값
        inference_result = inference_results
        if "kv_result" in inference_results:
            inference_result = inference_results.get("kv_result", {})
        # logger.debug(f"{task_id}-inference results:\n{inference_results}")
        
        
        # convert preds to texts
        if (
            inputs.get("convert_preds_to_texts") is not None
            and "texts" not in inference_results
        ):
            
            logger.info("[{}] #5-1 try convert rec_preds to texts", datetime.now())
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            logger.info("[{}] #5-2 end convert rec_preds to texts (pp response status code: {})", datetime.now(), status_code)
            
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3503)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            inference_results["texts"] = texts

        # TODO: pp에서 tsbl_sort를 못할경우 얘를 쓰자
        # tsbl_sort_result = sort_text_tblr(inference_result)
        doc_type_code = inference_results.get("doc_type")
        
        # Post processing
        # 미래과학아카데미는 ocr일경우 줄글 pp로 이동
        if inputs.get("route_name", "ocr") == 'ocr':
            
            logger.info("[{}] #6-1 try general_pp for fsa", datetime.now())
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client,
                task_id=task_id,
                response_log=response_log,
                inputs=inference_result,
                post_processing_type="general_pp",
            )            
            logger.info("[{}] #6-2 end general_pp for fs (pp response status code: {})", datetime.now(), status_code)
            
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3502)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            
            text_merged = post_processing_results.get('result').get('text').get('text')

            inference_results.update({
                "text_merged": text_merged
            })                

    
    response_log.update(inference_results.get("response_log", {}))
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")

    inference_id = get_ts_uuid("inference")
    doc_type_code = inference_results.get("doc_type")
    
    # doc_type_code로 doc_type_index 조회
    
    logger.info("[{}] #7-1 try select doc type info from db", datetime.now())
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    logger.info("[{}] #7-2 end select doc type info from db (doc_type: {})", datetime.now(), type(select_doc_type_result))
    
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_idx = select_doc_type_result.doc_type_idx

    inference_results.update(doc_type=select_doc_type_result)

    logger.info("[{}] #8-1 try insert inference_result to db", datetime.now())
    insert_inference_result = query.insert_inference(
        session=session,
        inference_id=inference_id,
        document_id=document_id, 
        user_email=user_email,
        user_team=user_team,
        inference_result=inference_results,
        inference_type=inputs.get("inference_type"),
        page_num=inference_results.get("page", target_page),
        doc_type_idx=doc_type_idx,
        response_log=response_log
    )
    logger.info("[{}] #8-2 end isnert inference_result to db (result: {})", datetime.now(), type(insert_inference_result))
    
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
    
    logger.info("#9-1 inference end at {}", datetime.now())
    logger.info("#9-2 end document_id: {}", document_id)
    
    return JSONResponse(content=jsonable_encoder(response))


# @TODO utils로 이동
def sort_text_tblr(inference_result: dict) -> Dict[str, list]:
    t_list = inference_result.get("texts", [])
    b_list = inference_result.get("boxes", [])
    s_list = inference_result.get("scores", [])
    c_list = inference_result.get("classes", [])
    
    s_list = s_list if len(s_list) > 0 else [ 0.0 for i in range(len(t_list)) ]
    c_list = c_list if len(c_list) > 0 else [ "" for i in range(len(t_list)) ]
    
    tbsc_list = [ (t, b, s, c) for t, b, s, c in zip(t_list, b_list, s_list, c_list) ]
    
    tbsc_list.sort(key= lambda x : (x[1][1], x[1][0]))
    
    t_list_, b_list_, s_list_, c_list_ = (list(), list(), list(), list())
    for tbsc in tbsc_list:
        t_list_.append(tbsc[0])
        b_list_.append(tbsc[1])
        s_list_.append(tbsc[2])
        c_list_.append(tbsc[3])
    
    return dict(
        texts=t_list_,
        boxes=b_list_,
        scores=s_list_,
        classes=c_list_
    )
