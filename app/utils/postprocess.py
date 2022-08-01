from typing import Dict

from sqlalchemy.orm import Session
from app.database import query, schema

UNRECOGNITION_KV_ITEM = {
    "text":"",
    "score":0.0,
    "class": "",
    "box": [0.0, 0.0, 0.0, 0.0],
    "merged_count": 0
}

def add_unrecognition_kv(session: Session, select_inference_result: schema.InferenceInfo):
    # 인식 되지 않은 class None값으로 추가
    kv_class_codes = select_inference_result.inference_result.get("kv").keys()
    
    doc_type_idx = select_inference_result.doc_type_idx
    select_doc_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    
    # @TODO pp_server로 이동
    if select_inference_result.inference_result.get("doc_type", "None") in ["FN-OIP", "FN-BP"]:
        modif_class_code(select_inference_result)
    
    maximun_kv_code = [ x.kv_class_code for x in select_doc_kv_result ]
    
    unrecognition_kv_item = dict()
    unrecognition_kv_item.update(UNRECOGNITION_KV_ITEM)
    
    unrecognition_kv = dict()
    for kv_code in maximun_kv_code:
        if kv_code in kv_class_codes: continue
        
        unrecognition_kv_item.update({"class":kv_code})
        
        unrecognition_kv[kv_code] = unrecognition_kv_item
        select_inference_result.inference_result["kv"][kv_code] = unrecognition_kv_item
    
    
    return select_inference_result, unrecognition_kv


def add_class_name_kr(session: Session, select_inference_result: schema.InferenceInfo):
    doc_type_idx = select_inference_result.doc_type_idx
    select_doc_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    
    class_kr_dict = { d.kv_class_info.kv_class_code : d.kv_class_info.kv_class_name_kr for d in select_doc_kv_result }
    
    kv_class_codes = select_inference_result.inference_result.get("kv").keys()
    for class_code in kv_class_codes:
        if class_code not in class_kr_dict.keys(): continue
        
        select_inference_result.inference_result["kv"][class_code]["class_name"] = class_kr_dict[class_code]
    
    
    return select_inference_result


def modif_class_code(select_inference_result: schema.InferenceInfo) -> None:
    doc_type_code: str = select_inference_result.inference_result.get("doc_type")
    doc_type_code_sub = "-" + doc_type_code.split("-")[1] + "-"
    
    inference_result_kv_ : Dict[str, dict] = dict()
    inference_result_kv: Dict[str, dict] = select_inference_result.inference_result.get("kv", {})
    for kv_key, kv_value in inference_result_kv.items():
        
        if kv_key == "NONE": continue
        
        kv_class_doc_type_code_sub = "-" + kv_key.split("-")[1] + "-"
        
        kv_key_modif = kv_key.replace(kv_class_doc_type_code_sub, doc_type_code_sub)
        kv_value.update({"class":kv_key_modif})
        
        inference_result_kv_.update({kv_key_modif:kv_value})
    
    
    select_inference_result.inference_result.update(kv=inference_result_kv_)