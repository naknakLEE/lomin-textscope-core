from fastapi import Request
from typing import Dict
from app.database import query

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
    "customer": "textscope"
}
DEFAULT_GOCR_PARAMS = {
    "use_general_ocr": True,
    "convert_preds_to_texts": True,
}
DEFAULT_CLS_PARAMS = {
    "use_general_ocr": False, 
    "route_name": "longinus",
    "cls_threshold": None
}
DEFAULT_CLSKV_PARAMS = {
    "use_general_ocr": False,
    "convert_preds_to_texts": True,
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

def bg_ocr(request: Request, current_user: UserInfoInModel, /, **kwargs: Dict):
    document_id = kwargs.get("document_id")
    document_pages = kwargs.get("document_pages", 1)
    document_path = kwargs.get("save_path")
    doc_type_code = kwargs.get("doc_type_code")
    
    ocr_params = dict()
    ocr_params.update(DEFAULT_PARAMS)
    
    
    if doc_type_code is not None: # CLSKV
        ocr_params.update(DEFAULT_CLSKV_PARAMS)
        ocr_params.get("hint", {}).get("doc_type", {}).update(doc_type=doc_type_code)
    else: # GOCR
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
