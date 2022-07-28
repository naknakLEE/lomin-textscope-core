from sqlalchemy.orm import Session
from app.database import query

def add_unrecognition_kv(session: Session, select_inference_result: dict):
    # 인식 되지 않은 class None값으로 추가
    kv_class_codes = select_inference_result.inference_result.get("kv").keys()
    
    doc_type_idx = select_inference_result.doc_type_idx
    select_doc_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    maximun_kv_code = []
    for d in select_doc_kv_result:
        maximun_kv_code.append(d.kv_class_code)
        
    for max_kv_code in maximun_kv_code:
        if max_kv_code not in kv_class_codes:
            select_inference_result.inference_result["kv"][max_kv_code] = {
                "text": "",
                "score": 0,
                "class": max_kv_code,
                "box": [0,0,0,0],
                "merged_count": 0,
            }
    return select_inference_result

def add_class_name_kr(session: Session, select_inference_result):
    kv_class_codes = select_inference_result.inference_result.get("kv").keys()
    select_kv_class_result = query.select_kv_class_info_get_all_multi(session, kv_class_code=kv_class_codes)
    for class_code, kv_class_object in zip(kv_class_codes, select_kv_class_result):
        select_inference_result.inference_result["kv"][class_code]["class_name"] = kv_class_object.kv_class_name_kr
    return select_inference_result