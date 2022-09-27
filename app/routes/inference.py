from httpx import Client
import unicodedata

from typing import Dict, List, Union
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
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict, get_company_group_prefix
from app.utils.logging import logger
from app.utils.document import (
    save_upload_document,
    get_stored_file_extension
)
from app.utils.image import (
    read_image_from_bytes,
    get_image_bytes,
    image_to_base64,
)
from app.wrapper import pp, pipeline, settings
from app.database import query, schema
from app.database.connection import db
from app.schemas import error_models as ErrorResponse
from app.middlewares.exception_handler import CoreCustomException
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
) -> Union[JSONResponse, dict]:
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
    
    if inputs.get("doc_type_idx") is not None:
        inputs = ocr_kv(inputs, current_user, session)
    
    if inputs.get("angle", 0) != 0:
        inputs = ocr_angle(inputs, current_user, session)
    
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
    
    group_prefix = get_company_group_prefix(session, user_email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    select_log_result = query.select_log(session, log_id=task_id) 
    if isinstance(select_log_result, schema.LogInfo):
        raise CoreCustomException(2202)
    elif isinstance(select_log_result, JSONResponse):
        status_code_no_log, _ = ErrorResponse.ErrorCode.get(2201)
        if select_log_result.status_code != status_code_no_log:
            return select_log_result
    
    logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    insert_log_result = query.insert_log(
        session=session,
        log_id=task_id,
        log_type=group_prefix + "OCR_REQUEST",
        user_email=user_email,
        user_team=user_team,
        log_content=dict({"request": inputs})
    )
    
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
            raise CoreCustomException(3501)
        
        if "texts" in inference_results.keys():
            inference_results.update(texts= [ unicodedata.normalize('NFKC', x) for x in inference_results.get("texts", []) ] )
            inference_results.update(
                texts= [
                    x.replace("[UNK]", "").replace('\"', "").replace("\\", "")
                    for x in inference_results.get("texts", [])
                ]
            )
            inference_results.update(sort_text_tblr(inference_results))
        
        # inference_result: response 생성에 필요한 값, inference_results: response 생성하기 위한 과정에서 생성된 inference 결과 포함한 값
        inference_result = inference_results
        if "kv_result" in inference_results:
            inference_result = inference_results.get("kv_result", {})
        logger.debug(f"{task_id}-inference results:\n{inference_results}")
        
        
        # convert preds to texts
        if (
            inputs.get("convert_preds_to_texts", False) is True
            and "texts" not in inference_results
        ):
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                raise CoreCustomException(3503)
            inference_results["texts"] = texts
        
        doc_type_code = inference_results.get("doc_type")
        
        # Post processing
        post_processing_type = get_pp_api_name(doc_type_code)
        if post_processing_type is not None \
            and doc_type_code is not None \
            and inputs.get("route_name", None) != 'cls':
            
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
                doc_type=doc_type_code,
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
                raise CoreCustomException(3502)
            
            inference_results["kv"] = post_processing_results["result"]
            inference_results.update(parse_kv_class(session, inference_result))
            inference_results.update(sort_kv_tblr(inference_results))
            logger.info(
                f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
            )
            if "texts" not in inference_results:
                inference_results["texts"] = post_processing_results["texts"]
                logger.info(
                    f'{task_id}-post-processed text result:\n{pretty_dict(inference_results.get("texts", {}))}'
                )
    
    response_log.update(inference_results.get("response_log", {}))
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")
    
    inference_id = get_ts_uuid("inference")
    doc_type_code = doc_type_code if doc_type_code not in ["NONE", None] else "GOCR"
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_idx = select_doc_type_result.doc_type_idx
    
    if inputs.get("angle", 0) != 0:
        inference_results.update(angle=inputs.get("angle", 0))
    
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
    if isinstance(insert_inference_result, JSONResponse):
        return insert_inference_result
    del insert_inference_result
    
    response = dict(
        response_log=response_log,
        inference_results=inference_results
    )
    response.update(
        resource_id=dict(
            # log_id=task_id
        )
    )
    
    if inputs.get("background", False): return response
    
    
    return JSONResponse(content=jsonable_encoder(response))


def ocr_angle(inputs: dict, current_user: UserInfoInModel, session: Session) -> Union[dict, JSONResponse]:
    document_id = inputs.get("document_id", "")
    page_num = inputs.get("page", 1)
    angle = inputs.get("angle")
    
    angle = -angle
    inputs.update(angle=angle)
    
    # 유저 정보 확인
    select_user_result = query.select_user(session, user_email=current_user.email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # 문서의 page_num 페이지의 썸네일 base64로 encoding
    document_extension = get_stored_file_extension(select_document_result.document_path)
    document_path = Path(str(page_num) + document_extension)
    document_bytes = get_image_bytes(document_id, document_path)
    angle_image = read_image_from_bytes(document_bytes, document_path.name, angle, page_num)
    if angle_image is None:
        raise CoreCustomException(2103)
    
    document_data = image_to_base64(angle_image)
    
    document_name = "_".join([str(page_num), str(angle)])
    document_name += document_path.suffix
    
    # 문서 저장(minio or local pc)
    save_success, save_path, pages = save_upload_document(document_id, document_name, document_data, new_document=False)
    
    if save_success is False:
        raise CoreCustomException(4102, "문서")
    
    inputs.update(
        documnet_path=document_name,
        rectify=dict(
            rotation_90n=False,
            rotation_fine=False
        )
    )
    
    return inputs


def ocr_kv(inputs: dict, current_user: UserInfoInModel, session: Session) -> Union[dict, JSONResponse]:
    document_id = inputs.get("document_id", "")
    doc_type_idx = inputs.get("doc_type_idx")
    page_num = inputs.get("page", 1)
    
    # 유저 정보 확인
    select_user_result = query.select_user(session, user_email=current_user.email)
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team = select_user_result.user_team
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 요청한 page_num이 1보다 작거나, 총 페이지 수보다 크면 에러 응답 반환
    if page_num < 1 or select_document_result.document_pages < page_num:
        raise CoreCustomException(2506)
    
    # 요청한 doc_type_idx 가 0 또는 31이면 route_name을 gocr로 변경
    if doc_type_idx == 0 or doc_type_idx == 31:
        inputs.update(route_name="gocr")
    
    # doc_type_idx로 doc_type_code 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_idx=doc_type_idx)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_code = select_doc_type_result.doc_type_code
    
    doc_type_idxs: dict = select_document_result.doc_type_idxs
    
    doc_type_idx_list: list = doc_type_idxs.get("doc_type_idxs", [])
    doc_type_idx_list.pop(page_num - 1)
    doc_type_idx_list.insert(page_num - 1, doc_type_idx)
    
    doc_type_codes_list: list = doc_type_idxs.get("doc_type_codes", [])
    doc_type_codes_list.pop(page_num - 1)
    doc_type_codes_list.insert(page_num - 1, doc_type_code)
    
    select_doc_type_cls_group_result = query.select_doc_type_cls_group(session, cls_idx=select_document_result.cls_idx)
    select_doc_type_cls_group_result: List[schema.DocTypeClsGroup]
    cls_type_doc_type = [ x.doc_type_idx for x in select_doc_type_cls_group_result ]
    
    doc_type_cls_match: List[int] = list()
    for doc_type_idx in doc_type_idx_list:
        if doc_type_idx in cls_type_doc_type:
            doc_type_cls_match.append(doc_type_idx)
        else:
            doc_type_cls_match.append(31)
    
    query.update_document(
        session,
        document_id,
        doc_type_idxs=dict(
            doc_type_idxs=doc_type_idx_list,
            doc_type_codes=doc_type_codes_list
        ),
        doc_type_idx=doc_type_idx_list,
        doc_type_code=doc_type_codes_list,
        doc_type_cls_match=doc_type_cls_match
    )
    
    inputs.update(
        hint=dict(
            doc_type=dict(
                use=True,
                trust=True,
                doc_type=doc_type_code
            ),
            key_value=[]
        )
    )
    
    return inputs

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

# @TODO utils로 이동
def sort_kv_tblr(inference_result: dict) -> Dict:
    z_b = [0, 0, 0, 0]
    
    kv: Dict[str, Dict] = inference_result.get("kv", {})
    kv_list = [ (k, v) for k, v in kv.items() if k.endswith("_VALUE") ]
    
    kv_list.sort(key= lambda x : (x[1].get("box", z_b)[1], x[1].get("box", z_b)[0]))
    for order, kv_ in enumerate(kv_list):
        kv.get(kv_[0], {}).update(order=order+1)
    
    return dict(
        kv=kv
    )

# @TODO utils로 이동
def parse_kv_class(session: Session, inference_result: dict) -> Dict:
    doc_type_code = inference_result.get("doc_type")
    doc_type_code = doc_type_code if doc_type_code not in ["NONE", None] else "GOCR"
    
    # doc_type_code로 doc_type_index 조회
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_idx = select_doc_type_result.doc_type_idx
    
    select_doc_kv_result: List[schema.DocTypeKvClass] = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    select_doc_kv_result = [ x for x in select_doc_kv_result if x.kv_class_info.kv_class_use == "false" ]
    
    kv = inference_result.get("kv", {})
    for no_use_kv_class in [ x.kv_class_code for x in select_doc_kv_result ]:
        kv.pop(no_use_kv_class, None)
    
    return dict(
        kv=kv
    )
