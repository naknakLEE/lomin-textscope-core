from datetime import datetime
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Body
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from typing import List, Dict

from sqlalchemy.orm import Session

from app import models
from app.database import schema, query
from app.database.connection import db
from app.common.const import get_settings
from app.middlewares.exception_handler import CoreCustomException
from app.utils.auth import get_current_active_user
from app.utils.utils import get_company_group_prefix
from app.utils.ocr_to_pdf import PdfParser, Word
from app.utils.image import (
    read_image_from_bytes,
    get_image_bytes
)
from app.utils.document import get_stored_file_extension


from app.utils.utils import cal_time_elapsed_seconds
from app.utils.utils import load_image2base64, basic_time_formatter


settings = get_settings()
router = APIRouter()
pdfparser = PdfParser()

@router.get("/")
def get_all_prediction(session: Session = Depends(db.session)) -> JSONResponse:
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    predictions = list()

    gocr_results = query.select_inference_by_type(session, inference_type="gocr")
    kv_results = query.select_inference_by_type(session, inference_type="kv")

    for gocr_res in gocr_results:
        inference_result = gocr_res.inference_result
        inference_type = gocr_res.inference_type
        image_pkey = gocr_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        image_path = image.image_path

        texts = list()
        for text_, box_, score_, class_ in zip(
            inference_result["texts"],
            inference_result["boxes"],
            inference_result["scores"],
            inference_result["classes"],
        ):
            bbox = models.Bbox(
                x=box_[0],
                y=box_[1],
                w=box_[2] - box_[0],
                h=box_[3] - box_[1],
            )
            # TODO: kv_ids 매핑 필요
            text = models.Text(
                id=class_, text=text_, bbox=bbox, confidence=score_, kv_ids=[class_]
            )
            texts.append(text)

        prediction = dict(
            image_path=image_path,
            inference_result=dict(texts=texts),
            inference_type=inference_type,
        )
        predictions.append(prediction)

    for kv_res in kv_results:
        inference_result = kv_res.inference_result
        inference_type = kv_res.inference_type
        image_pkey = kv_res.image_pkey
        image = query.select_image_by_pkey(session, image_pkey=image_pkey)
        category = query.select_category_by_pkey(
            session, category_pkey=image.category_pkey
        )
        image_path = image.image_path
        image_category = category.category_name
        kv = inference_result.get("kv", {})
        key_values = list()
        texts = list()

        for key, value in kv.items():
            if not key.endswith("_pred") or not value:
                continue
            bbox = models.Bbox(
                x=value["box"][0],
                y=value["box"][1],
                w=value["box"][2] - value["box"][0],
                h=value["box"][3] - value["box"][1],
            )
            # TODO: key, kv_ids 매핑 필요
            key_value = models.KeyValue(
                id=value["class"],
                key=key,
                confidence=value["score"],
                text=value["value"],
                bbox=bbox,
                is_hint_used=False,
                is_hint_trusted=False,
            )
            key_values.append(key_value)

        texts = list()
        for text_, box_, score_, class_ in zip(
            inference_result["texts"],
            inference_result["boxes"],
            inference_result["scores"],
            inference_result["classes"],
        ):
            bbox = models.Bbox(
                x=box_[0],
                y=box_[1],
                w=box_[2] - box_[0],
                h=box_[3] - box_[1],
            )
            # TODO: kv_ids 매핑 필요
            text = models.Text(
                id=class_, text=text_, bbox=bbox, confidence=score_, kv_ids=[class_]
            )
            texts.append(text)

        prediction = dict(
            image_path=image_path,
            inference_result=dict(
                doc_type=image_category, key_values=key_values, texts=texts
            ),
            inference_type=inference_type,
        )
        predictions.append(prediction)

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)

    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            predictions=predictions,
        )
    )

    response = dict(predictions=predictions, response_log=response_log)

    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/cls-kv")
def get_cls_kv_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    request_datetime = datetime.now()
    response = dict()
    response_log = dict()

    kv_result = query.select_kv_inference_from_taskid(session, task_id=task_id)
    if kv_result is None:
        # @FIXME: kv prediction 값이 없을 경우에 대한 예외처리
        raise HTTPException(status_code=400)
    inference_type = kv_result.inference_type
    inference_result: Dict = kv_result.inference_result
    response_log = inference_result.get("response_log", {})
    started_datetime = basic_time_formatter(
        response_log.get("time_textscope_request", "")
    )
    finished_datetime = basic_time_formatter(
        response_log.get("time_textscope_response", "")
    )
    kv: Dict = inference_result.get(inference_type, {})

    doc_type = models.DocType(
        code=inference_result.get("doc_type", "").split("_")[0],
        name=inference_result.get("doc_type", "").split("_")[-1],
        confidence=0.93,
        is_hint_used=False,
        is_hint_trusted=False,
    )
    key_values: List = list()
    texts: List = list()

    for key, value in kv.items():
        if not key.endswith("_pred") or not value:
            continue
        if "key_pred" in key:
            continue
        bbox = models.Bbox(
            x=value["box"][0],
            y=value["box"][1],
            w=value["box"][2] - value["box"][0],
            h=value["box"][3] - value["box"][1],
        )
        # TODO: key, kv_ids 매핑 필요
        key_value = models.KeyValue(
            id=value["class"],
            key=key,
            confidence=value["score"],
            text=value["value"],
            bbox=bbox,
            is_hint_used=False,
            is_hint_trusted=False,
        )
        key_values.append(key_value)

    prediction = models.PredictionResponse(
        doc_type=doc_type, key_values=key_values, texts=texts
    )

    # @TODO: select task status from db
    task = models.Task(
        task_id=task_id,
        status_code="ST-TRN-CLS-0003",
        status_message="학습 task 완료",
        progress=1.0,
        started_datetime=started_datetime,
        finished_datetime=finished_datetime,
    )

    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)
    if inference_img_path is None:
        # @FIXME: 예외처리 추가
        raise HTTPException(status_code=400)

    # @FIXME: client에서 image visualize를 하는 부분이 따로 존재해서 제거 해도 될듯?
    img_str = load_image2base64(inference_img_path)

    image = None

    if visualize:
        image = img_str

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)

    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            prediction=prediction,
            task=task,
            image=image,
        )
    )

    response.update(
        dict(response_log=response_log, prediction=prediction, task=task, image=image)
    )

    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/gocr")
def get_gocr_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    request_datetime = datetime.now()
    response = dict()
    response_log = dict()

    text = models.Text()

    # @TODO: select prediction result from db
    prediction = models.BaseTextsResponse(texts=[text])

    # @TODO: select task status from db
    task = models.Task(
        task_id=task_id,
        status_code="ST-TRN-CLS-0003",
        status_message="학습 task 완료",
        progress=1.0,
        started_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        finished_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    )

    inference_img_path = query.select_inference_img_path_from_taskid(session, task_id)
    if inference_img_path is None:
        # @FIXME: 예외처리 추가
        raise HTTPException(status_code=400)

    img_str = load_image2base64(inference_img_path)

    image = None

    if visualize:
        image = img_str
    else:
        image = None

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)

    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            prediction=prediction,
            task=task,
            image=image,
        )
    )

    response.update(
        dict(response_log=response_log, prediction=prediction, task=task, image=image)
    )

    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/download/documents/pdf")
def get_document_info_inference_pdf(
    document_id:   str,
    pdf_file_name:      str,
    text_type:     str,
    apply_inspect: bool,
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user)
):
    """
    특정 문서의 gocr 또는 kv 인식 결과를 searchablePDF로 저장합니다.
    """
    user_email:    str  = current_user.email
    
    # 사용자 권한(정책) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=user_email)
    if isinstance(user_policy_result, JSONResponse):
        return user_policy_result
    user_policy_result: dict = user_policy_result
    
    # 사용자가 사원인지 확인하고 맞으면 company_code를 group_prefix로 가져옴
    group_prefix = get_company_group_prefix(session, current_user.email)
    if isinstance(group_prefix, JSONResponse):
        return group_prefix
    group_prefix: str = group_prefix
    
    user_team_list: List[str] = list()
    user_team_list.extend(user_policy_result.get("R_DOCX_TEAM", []))
    group_list = list(set( [ group_prefix + x for x in user_team_list ] ))
    
    # 문서 정보 조회
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        return select_document_result
    select_document_result: schema.DocumentInfo = select_document_result
    
    # 사용자 정책(조회 가능 문서 종류(대분류)) 확인
    cls_code_list: List[str] = list()
    cls_code_list.extend(user_policy_result.get("R_DOC_TYPE_CLASSIFICATION", []))
    cls_code_list = list(set( [ group_prefix + x for x in cls_code_list ] ))
    
    cls_type_idx_list_result = query.get_user_classification_type(session, cls_code_list=cls_code_list)
    if isinstance(cls_type_idx_list_result, JSONResponse):
        return cls_type_idx_list_result
    
    cls_type_idx_result_list: Dict[int, dict] = { x.get("index") : x for x in cls_type_idx_list_result }
    
    # 사용자 정책(조회 가능 문서 종류(소분류)) 확인
    doc_type_idx_code: Dict[int, dict] = dict()
    for cls_type_info in cls_type_idx_result_list.values():
        for doc_type_info in cls_type_info.get("docx_type", []):
            doc_type_idx_code.update({doc_type_info.get("index"):doc_type_info})
    
    # 해당 문서에 대한 권한이 없음
    if group_prefix + select_document_result.user_team not in group_list:
        raise CoreCustomException(2505)
    
    wordss: List[List[Word]] = list()
    images: List[Image.Image] = list()
    for page_num in range(1, select_document_result.document_pages + 1):
        # document_id로 특정 페이지의 가장 최근 inference info 조회
        select_inference_result = query.select_inference_latest(session, document_id=document_id, page_num=page_num)
        if isinstance(select_inference_result, JSONResponse):
            return select_inference_result
        select_inference_result: schema.InferenceInfo = select_inference_result
        inference_id = select_inference_result.inference_id
        angle = select_inference_result.inference_result.get("angle", 0)
        
        # 가장 최근 inspect 결과가 있으면 가져오기
        select_inspect_result = None
        if apply_inspect is True:
            select_inspect_result = query.select_inspect_latest(session, inference_id=inference_id)
            if isinstance(select_inspect_result, JSONResponse):
                return select_inspect_result
            select_inspect_result: schema.InspectInfo = select_inspect_result
            
            if select_inspect_result is not None:
                angle = select_inspect_result.inspect_result.get("angle", 0)
        
        text_type = "kv"
        if select_inference_result.doc_type_idx == 0 \
            or select_inference_result.doc_type_idx not in doc_type_idx_code.keys():
            
            text_type = "gocr"
        
        words: List[Word] = list()
        if text_type == "kv":
            kv = None
            if select_inspect_result is not None and apply_inspect is True:
                kv = select_inspect_result.inspect_result.get("kv", {})
            else:
                kv = select_inference_result.inference_result.get("kv", {})
            
            for k, v in kv.items():
                if k.endswith("_KEY"): continue
                words.append(Word(text=v.get("text", ""), bbox=v.get("box", [0., 0., 0., 0.])))
        
        else: # text_type == "gocr":
            gocr = None
            if select_inspect_result is not None and apply_inspect is True:
                gocr = select_inspect_result.inspect_result
            else:
                gocr = select_inference_result.inference_result
            
            for text, box in zip (gocr.get("texts", []), gocr.get("boxes", [])):
                words.append(Word(text=text, bbox=box))
        
        wordss.append(words)
        
        # 문서의 page_num 페이지의 썸네일 base64로 encoding
        document_extension = get_stored_file_extension(select_document_result.document_path)
        document_path = Path(str(page_num) + document_extension)
        document_bytes = get_image_bytes(document_id, document_path)
        images.append(read_image_from_bytes(document_bytes, document_path.name, angle, page_num))
    
    content: bytes = pdfparser.export_pdf(wordss, images)
    
    
    return Response(
        content=content,
        headers={'Content-Disposition': f'attachment; filename="{pdf_file_name}.pdf"'},
        media_type="application/pdf"
    )