from typing import Dict

from fastapi import Request
from fastapi.responses import JSONResponse

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
        'rotation_90n': False, 
        'rotation_fine': False
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


def bg_gocr(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict):
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    ocr_params = dict()
    ocr_params.update(DEFAULT_PARAMS)
    ocr_params.update(DEFAULT_GOCR_PARAMS)
    
    session = next(db.session())
    
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        ocr_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=document_path,
        )
        
        ocr(request=request, inputs=ocr_params, current_user=current_user, session=session)
    
    query.update_document(session, document_id, inspect_id="NOT_INSPECTED")


def bg_cls(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict):
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    # cls_model_info에 따라 어떤 cls모델을 사용할지는 추 후 논의
    cls_model_info: schema.ModelInfo = kwargs.get("cls_model_info")
    
    session = next(db.session())
    
    ocr_params = dict()
    ocr_params.update(DEFAULT_PARAMS)
    
    if cls_model_info is not None:
        ocr_params.update(DEFAULT_CLS_PARAMS)
    
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        ocr_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=document_path,
        )
        
        ocr(request=request, inputs=ocr_params, current_user=current_user, session=session)
    
    query.update_document(session, document_id, inspect_id="NOT_INSPECTED")


def bg_kv(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict):
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    # doc_type에 따라 어떤 kv모델을 사용할지는 추 후 논의
    doc_type_info: schema.DocTypeInfo = kwargs.get("doc_type_info")
    
    session = next(db.session())
    
    ocr_params = dict()
    ocr_params.update(DEFAULT_PARAMS)
    
    if doc_type_info is not None: # KV만 한다
        ocr_params.update(DEFAULT_KV_PARAMS)
        ocr_params.get("hint", {}).get("doc_type", {}).update(doc_type=doc_type_info.doc_type_code)
    
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        ocr_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=document_path,
        )
        
        ocr(request=request, inputs=ocr_params, current_user=current_user, session=session)
    
    query.update_document(session, document_id, inspect_id="NOT_INSPECTED")


def bg_clskv(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict):
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    
    # cls_model_info에 따라 어떤 cls모델을 사용할지는 추 후 논의
    cls_model_info: schema.ModelInfo = kwargs.get("cls_model_info")
    
    session = next(db.session())
    
    cls_params = dict()
    cls_params.update(DEFAULT_PARAMS)
    
    kv_params = dict()
    kv_params.update(DEFAULT_PARAMS)
    
    if cls_model_info is not None:
        cls_params.update(DEFAULT_CLS_PARAMS)
    
    for page in range(1, document_pages + 1):
        task_id=get_ts_uuid("task")
        
        cls_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=document_path,
        )
        
        cls_response: dict = ocr(
            request=request,
            inputs=cls_params,
            current_user=current_user,
            session=session
        )
        
        doc_type_info: str = cls_response.get("inference_results", {}).get("doc_type")
        
        if doc_type_info is not None:
            kv_params.update(DEFAULT_KV_PARAMS)
            kv_params.get("hint", {}).get("doc_type", {}).update(doc_type=doc_type_info)
        
        kv_params.update(
            task_id=task_id,
            request_id=task_id,
            document_id=document_id,
            page=page,
            document_path=document_path,
        )
        
        ocr(request=request, inputs=kv_params, current_user=current_user, session=session)
    
    query.update_document(session, document_id, inspect_id="NOT_INSPECTED")
