from typing import Dict, List

from sqlalchemy.orm import Session
from app.database import query, schema

UNRECOGNITION_KV_ITEM = {
    "text":"",
    "score":0.0,
    "class": "",
    "box": [0.0, 0.0, 0.0, 0.0],
    "merged_count": 0,
    "order": 0
}

# 인식 되지 않은 kv_class UNRECOGNITION_KV_ITEM으로 추가
def add_unrecognition_kv(session: Session, select_inference_result: schema.InferenceInfo):
    doc_type_idx = select_inference_result.doc_type_idx
    select_doc_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    select_doc_kv_result = [ x for x in select_doc_kv_result if x.kv_class_info.kv_class_use == "true" ]
    
    # @TODO pp_server로 이동
    del_class_code(select_inference_result)
    
    if select_inference_result.inference_result.get("doc_type", "NONE") in ["FN-OIP", "FN-BP"]:
        modif_class_code(select_inference_result)
    
    inference_result_kv = dict()
    unrecognition_kv = dict()
    kv_item = dict()
    kv_item.update(UNRECOGNITION_KV_ITEM)
    
    kv_class_codes = select_inference_result.inference_result["kv"].keys()
    for kv_class in select_doc_kv_result:
        if kv_class.kv_class_code in kv_class_codes:
            inference_result_kv[kv_class.kv_class_code] = select_inference_result.inference_result["kv"][kv_class.kv_class_code]
        else:
            kv_item.update({"class":kv_class.kv_class_code})
            inference_result_kv[kv_class.kv_class_code] = kv_item.copy()
            unrecognition_kv[kv_class.kv_class_code] = kv_item.copy()
        
        if kv_class.sequence is not None:
            inference_result_kv[kv_class.kv_class_code].update(order=kv_class.sequence)
    
    select_inference_result.inference_result["kv"] = inference_result_kv
    
    return select_inference_result, unrecognition_kv


def add_class_name_kr(session: Session, select_inference_result: schema.InferenceInfo):
    doc_type_idx = select_inference_result.doc_type_idx
    select_doc_kv_result = query.select_doc_type_kv_class_get_all(session, doc_type_idx=doc_type_idx)
    
    kv_class_dict = { d.kv_class_info.kv_class_code : d.kv_class_info for d in select_doc_kv_result }
    
    inference_result_ = dict()
    for class_code, v in select_inference_result.inference_result["kv"].items():
        class_name_kr = kv_class_dict.get(class_code, schema.KvClassInfo()).kv_class_name_kr
        if class_name_kr is None: continue
        v.update(class_name=class_name_kr)
        
        inference_result_.update({class_code:v})
    
    select_inference_result.inference_result.update(kv=inference_result_)
    
    return select_inference_result


def modif_class_code(select_inference_result: schema.InferenceInfo) -> None:
    modif_doc_type_code = select_inference_result.inference_result.get("doc_type")
    
    inference_result_kv_ = dict()
    for kv_key, kv_value in select_inference_result.inference_result["kv"].items():
        kv_key_modif = kv_key.replace("FN-OIP", modif_doc_type_code).replace("FN-BP", modif_doc_type_code)
        kv_value.update({"class":kv_key_modif})
        
        inference_result_kv_.update({kv_key_modif:kv_value})
    
    select_inference_result.inference_result.update(kv=inference_result_kv_)


def del_class_code(select_inference_result: schema.InferenceInfo, kv_class_code: str = "NONE") -> None:
    inference_result_kv_ = dict()
    for kv_key, kv_value in select_inference_result.inference_result["kv"].items():
        if kv_key == kv_class_code: continue
        kv_value.update({"class":kv_key})
        
        inference_result_kv_.update({kv_key:kv_value})
        
    select_inference_result.inference_result.update(kv=inference_result_kv_)