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
        
    unrecognition_kv = dict()
    for max_kv_code in maximun_kv_code:
        if max_kv_code not in kv_class_codes:
            select_inference_result.inference_result["kv"][max_kv_code] = {
                "text": "",
                "score": 0,
                "class": max_kv_code,
                "box": [0,0,0,0],
                "merged_count": 0,
            }
            unrecognition_kv[max_kv_code] =  {
                "text": "",
                "score": 0,
                "class": max_kv_code,
                "box": [0,0,0,0],
                "merged_count": 0,
            }
    return select_inference_result, unrecognition_kv

def add_class_name_kr(session: Session, select_inference_result):
    
    doc_type_idx = select_inference_result.doc_type_idx
    doc_type_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    
    class_kr_dict = {d.kv_class_info.kv_class_code: d.kv_class_info.kv_class_name_kr for d in doc_type_kv_result}
    
    kv_class_codes = select_inference_result.inference_result.get("kv").keys()
    for class_code in kv_class_codes:
        select_inference_result.inference_result["kv"][class_code]["class_name"] = class_kr_dict[class_code]
    return select_inference_result