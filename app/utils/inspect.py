from typing import Dict, List
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.utils.postprocess import add_unrecognition_kv
from app.database import schema, query
import copy


settings = get_settings()
doc_type_cls_group_dict: Dict[int, List[schema.DocTypeInfo]] = dict()


def get_inspect_accuracy(session: Session, select_inference_result: schema.InferenceInfo, inspect_result: dict):
    doc_type_code = select_inference_result.inference_result.get("doc_type")
    if doc_type_code in ["GOCR", "NONE", None]: # GOCR
        return None
    
    
    # 인식 되지 않은 class None값으로 추가
    
    _, unrecognition_kv = add_unrecognition_kv(session, copy.deepcopy(select_inference_result))
    inference_kv = select_inference_result.inference_result.get("kv")
    
    inspect_kv = inspect_result.get("kv")
    
    
    # _KEY, NONE 인식률에서 제거
    inspect_kv = copy.deepcopy(inspect_kv)
    for key in list(inspect_kv.keys()):
        if "_KEY" in key or "NONE" in key:
            del inspect_kv[key]

    # _KEY, NONE 인식률에서 제거   
    inference_kv = copy.deepcopy(inference_kv)
    for key in list(inference_kv.keys()):
        if "_KEY" in key or "NONE" in key:
            del inference_kv[key]
    
    # _KEY, NONE 인식률에서 제거
    unrecognition_kv = copy.deepcopy(unrecognition_kv)
    for key in list(unrecognition_kv.keys()):
        if "_KEY" in key or "NONE" in key:
            del unrecognition_kv[key]
    
    
    # 미검출 항목 수정 개수 확인
    modify_count_unrecognition = 0
    for k, v in unrecognition_kv.items():
        if inspect_kv[k]["text"] != unrecognition_kv[k]["text"] or \
            inspect_kv[k]["box"] != unrecognition_kv[k]["box"] or \
            inspect_kv[k]["merged_count"] != unrecognition_kv[k]["merged_count"] or \
            inspect_kv[k]["class"] != unrecognition_kv[k]["class"]:
            modify_count_unrecognition += 1
    
    # inference 결과(미검출 항목 제외) 수정 개수 확인
    modify_count_inference = 0
    for k, v in inference_kv.items():
        if inspect_kv[k]["text"] != inference_kv[k]["text"] or \
            inspect_kv[k]["box"] != inference_kv[k]["box"] or \
            inspect_kv[k]["merged_count"] != inference_kv[k]["merged_count"] or \
            inspect_kv[k]["class"] != inference_kv[k]["class"]:
            modify_count_inference += 1
    
    inference_kv_count = len(inference_kv)
    divide_parent = inference_kv_count + modify_count_unrecognition
    divide_child = divide_parent - (modify_count_unrecognition + modify_count_inference)
    inspect_accuracy = (divide_child / divide_parent) * 100
    
    return inspect_accuracy


def get_inspect_accuracy_avg(session: Session, select_document_info: schema.DocumentInfo) -> float:
    document_id = select_document_info.document_id
    document_pages = select_document_info.document_pages
    document_cls_idx = select_document_info.cls_idx
    
    if document_cls_idx not in doc_type_cls_group_dict.keys():
        for doc_type_cls_group in query.select_doc_type_cls_group(session, cls_idx=document_cls_idx):
            v = doc_type_cls_group_dict.get(doc_type_cls_group.cls_idx, [])
            v.append(doc_type_cls_group.doc_type_info)
            doc_type_cls_group_dict.update({doc_type_cls_group.cls_idx:v})
    
    inspect_accuracy_list = list()
    for inference_info in [ query.select_inference_latest(session, document_id=document_id, page_num=x) for x in range(1, document_pages + 1) ]:
        # 대분류(document_cls_idx)에 포함되어 있지 않은 소분류(doc_type_idx)면 평균 계산식에서 제외
        if inference_info.doc_type_idx not in [ x.doc_type_idx for x in doc_type_cls_group_dict.get(document_cls_idx, []) ]:
            document_pages -= 1
            continue
        
        res = query.select_inspect_latest(session, inference_id=inference_info.inference_id, inspect_status=settings.STATUS_INSPECTED)
        if res is None: continue
        inspect_accuracy_list.append(res.inspect_accuracy)
    
    if document_pages == 0: return None
    
    inspect_accuracy_list += [100.0] * ( document_pages - len(inspect_accuracy_list) )
    
    return sum(inspect_accuracy_list) / document_pages
