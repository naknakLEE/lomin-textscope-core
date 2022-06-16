
from fastapi import BackgroundTasks
from typing import Dict
from uuid import uuid4
from sqlalchemy.orm import Session

from app.routes.inference import ocr


def bg_run_ocr(background_tasks: BackgroundTasks, session: Session, input_params: Dict) -> None:
    
    task_id = str(uuid4())
    ocr_params={
        'document_path': str(input_params.get("save_path")), 
        'use_general_ocr': True, 
        'post_processing': None, 
        'convert_preds_to_texts': True, 
        'user_email': input_params.get("user_email"), 
        'task_id': task_id, 
        'document_id': input_params.get("document_id"), 
        'detection_score_threshold': 0.5, 
        'use_text_extraction': False, 
        'rectify': {
            'rotation_90n': True, 
            'rotation_fine': True
            }, 
        'page': 1, 
        'detection_resize_ratio': 1.0, 
        'doc_type': 'None', 
        'request_id': task_id, 
        'customer': 'textscope'
    }
    background_tasks.add_task(ocr, inputs=ocr_params, session=session)