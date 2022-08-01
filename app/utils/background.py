import json
from typing import Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.utils.logging import logger
from app import hydra_cfg
from app.database import query, schema
from app.database.connection import db
from app.routes.inference import ocr
from app.utils.utils import get_ts_uuid
from app.models import UserInfo as UserInfoInModel
from app.common.const import get_settings


settings = get_settings()

DEFAULT_PARAMS = {
    "document_id": None,
    "rectify": {
        'rotation_90n': True, 
        'rotation_fine': True
    },
    "page": 1,
    "use_text_extraction": False, 
    "detection_score_threshold": 0.3, 
    "detection_resize_ratio": 1.0,
    
    "use_general_ocr": None,
    "doc_type": None,
    "document_path": None,
    "task_id": None, # bg_ocr에서 생성 
    "request_id": None, # bg_ocr에서 생성 (task_id와 동일 값)
    "customer": "textscope",
    "background": True
}
DEFAULT_GOCR_PARAMS = {
    "use_general_ocr": True,
    "convert_preds_to_texts": True,
    "route_name": "ocr",
}
DEFAULT_CLS_PARAMS = {
    "use_general_ocr": False, 
    "route_name": "cls",
    "cls_threshold": 0.0
}
DEFAULT_KV_PARAMS = {
    "use_general_ocr": False,
    "convert_preds_to_texts": True,
    "route_name": "kv",
    "hint": {
        "doc_type": {
            "use": True,
            "trust": True,
            "doc_type": None # 어디선가 업데이트 필요
        },
        "key_value": [
            {
                "use": False,
                "trust": False,
                "key": None,
                "value": None
            },
        ]
    },
    "idcard_version": "v1"
}
NOT_INSPECTED = "NOT_INSPECTED"
INFERENCE_ERROR = "INFERENCE_ERROR"


def bg_ocr_wrapper(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict) -> None:
    # cls_model_info에 따라 어떤 cls모델을 사용할지는 추 후 논의
    cls_model_info: schema.ModelInfo = kwargs.get("cls_model_info")
    
    # doc_type에 따라 어떤 kv모델을 사용할지는 추 후 논의
    doc_type_info: schema.DocTypeInfo = kwargs.get("doc_type_info")
    
    # TODO 어떤 파라미터에 따라 어떤 ocr을 사용할지 정함, 로직 개선 필요
    bg_ocr = None
    if cls_model_info is None and doc_type_info.doc_type_idx == 0: # gocr
        bg_ocr = bg_gocr
    elif cls_model_info is None and doc_type_info.doc_type_idx != 0: # kv
        bg_ocr = bg_kv
    elif cls_model_info is not None and doc_type_info.doc_type_idx == 0: # cls
        bg_ocr = bg_clskv
    elif cls_model_info is not None and doc_type_info.doc_type_idx != 0: # clskv
        bg_ocr = bg_clskv
    
    bg_ocr(request, current_user, **kwargs)


def bg_gocr(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict) -> None:
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    gocr_params = dict()
    gocr_params.update(DEFAULT_PARAMS)
    gocr_params.update(DEFAULT_GOCR_PARAMS)
    
    session = next(db.session())
    
    update_document_info_doc_type_idxs(session, document_id, [])
    
    doc_type_list: List[str] = list()
    inspect_id = NOT_INSPECTED
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        gocr_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=str(page)+".png",
        )
        
        try:
            ocr(request=request, inputs=gocr_params, current_user=current_user, session=session)
            doc_type_list.append("None")
        except Exception as ex:
            logger.error(f"[INFERENCE_ERROR] {ex}")
            inspect_id = INFERENCE_ERROR
    
    update_document_info_doc_type_idxs(session, document_id, doc_type_list)
    query.update_document(session, document_id, inspect_id=inspect_id)

def bg_cls(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict) -> None:
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    session = next(db.session())
    
    cls_params = dict()
    cls_params.update(DEFAULT_PARAMS)
    cls_params.update(DEFAULT_CLS_PARAMS)
    
    update_document_info_doc_type_idxs(session, document_id, [])
    
    doc_type_list: List[str] = list()
    inspect_id = NOT_INSPECTED
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        cls_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=str(page)+".png",
        )
        
        try:
            cls_response = ocr(request=request, inputs=cls_params, current_user=current_user, session=session)
            doc_type_code: str = cls_response.get("inference_results", {}).get("doc_type")
            doc_type_list.append(doc_type_code)
            
        except Exception as ex:
            logger.error(f"[INFERENCE_ERROR] {ex}")
            inspect_id = INFERENCE_ERROR
    
    update_document_info_doc_type_idxs(session, document_id, doc_type_list)
    query.update_document(session, document_id, inspect_id=inspect_id)

def bg_kv(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict) -> None:
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    doc_type_info: schema.DocTypeInfo = kwargs.get("doc_type_info")
    
    session = next(db.session())
    
    kv_params = dict()
    kv_params.update(DEFAULT_PARAMS)
    
    if doc_type_info is not None:
        kv_params.update(DEFAULT_KV_PARAMS)
        kv_params.get("hint", {}).get("doc_type", {}).update(doc_type=doc_type_info.doc_type_code)
    
    inspect_id = NOT_INSPECTED
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        kv_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=str(page)+".png",
        )
        
        try:
            ocr(request=request, inputs=kv_params, current_user=current_user, session=session)
            
        except Exception as ex:
            logger.error(f"[INFERENCE_ERROR] {ex}")
            inspect_id = INFERENCE_ERROR
    
    query.update_document(session, document_id, inspect_id=inspect_id)

def bg_clskv(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict) -> None:
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    cls_model_info: schema.ModelInfo = kwargs.get("cls_model_info")
    
    session = next(db.session())
    
    cls_params = dict()
    cls_params.update(DEFAULT_PARAMS)
    
    params = dict()
    params.update(DEFAULT_PARAMS)
    
    if cls_model_info is not None:
        cls_params.update(DEFAULT_CLS_PARAMS)
    
    update_document_info_doc_type_idxs(session, document_id, [])
    
    doc_type_list: List[str] = list()
    inspect_id = NOT_INSPECTED
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        cls_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=str(page)+".png",
        )
        
        try:
            cls_response = ocr(request=request, inputs=cls_params, current_user=current_user, session=session) 
            
            doc_type_code: str = cls_response.get("inference_results", {}).get("doc_type")
            doc_type_list.append(doc_type_code)
            
            # cls결과 doc_type이 사용 가능한(kv 모델 유/무) 문서 종류(소분류)일 경우 kv요청
            if doc_type_code in hydra_cfg.document.doc_type:
                params.update(DEFAULT_KV_PARAMS)
                params.get("hint", {}).get("doc_type", {}).update(doc_type=doc_type_code)
                
            # 아닐 경우 gocr요청
            else:
                params.update(DEFAULT_GOCR_PARAMS)
            
            params.update(
                task_id=task_id,
                request_id=task_id,
                document_id=document_id,
                page=page,
                document_path=str(page)+".png",
            )
            
            ocr(request=request, inputs=params, current_user=current_user, session=session)
            
        except Exception as ex:
            logger.error(f"[INFERENCE_ERROR] {ex}")
            inspect_id = INFERENCE_ERROR
    
    update_document_info_doc_type_idxs(session, document_id, doc_type_list)
    query.update_document(session, document_id, inspect_id=inspect_id)


def update_document_info_doc_type_idxs(session: Session, document_id: str, doc_type_list: List[str]) -> None:
    doc_type_idx_code: Dict[str, int] = dict()
    
    select_doc_type_info_all_result = query.select_doc_type_all(session, doc_type_code=list(set(doc_type_list)))
    if isinstance(select_doc_type_info_all_result, JSONResponse):
        return
    
    select_doc_type_info_all_result: List[schema.DocTypeInfo] = select_doc_type_info_all_result
    
    for doc_type_info in select_doc_type_info_all_result:
        doc_type_idx_code.update({doc_type_info.doc_type_code:doc_type_info.doc_type_idx})
    
    doc_type_idxs: List[int] = list()
    for doc_type_code in doc_type_list:
        doc_type_idxs.append(doc_type_idx_code.get(doc_type_code))
    
    if len(doc_type_idxs) == 0: doc_type_idxs.append(0)
    if len(doc_type_list) == 0: doc_type_list.append("NONE")
    
    query.update_document(
        session,
        document_id,
        doc_type_idxs=dict(
            doc_type_idxs=doc_type_idxs,
            doc_type_codes=doc_type_list,
        )
    )
