from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.utils.postprocess import add_unrecognition_kv
from app.database import schema, query
import copy

settings = get_settings()


def get_inspect_accuracy(session: Session, select_inference_result: schema.InferenceInfo, inspect_result: dict):
    doc_type_code = select_inference_result.inference_result.get("doc_type")
    if doc_type_code in ["NONE", None]: # GOCR
        return 0
    
    
    # 인식 되지 않은 class None값으로 추가
    
    _, unrecognition_kv = add_unrecognition_kv(session, copy.deepcopy(select_inference_result))
    inference_kv = select_inference_result.inference_result.get("kv")
    
    inspect_kv = inspect_result.get("kv")
    
    
    # _KEY, NONE 인식률에서 제거
    for key in list(inspect_kv.keys()):
        if "_KEY" in key or "NONE" in key:
            del inspect_kv[key]

    # _KEY, NONE 인식률에서 제거   
    for key in list(inference_kv.keys()):
        if "_KEY" in key or "NONE" in key:
            del inference_kv[key]
    
    # _KEY, NONE 인식률에서 제거
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
    document_pages = select_document_info.document_pages
    
    inspect_accuracy_list = list()
    for inference_id in [ query.select_inference_latest(session, page_num=x).inference_id for x in range(1, document_pages + 1) ]:
        res = query.select_inspect_latest(session, inference_id=inference_id, inspect_status=settings.STATUS_INSPECTED)
        if res is None: continue
        inspect_accuracy_list.append(res.inspect_accuracy)
    
    inspect_accuracy_list += [100.0] * ( document_pages - len(inspect_accuracy_list))
    
    return sum(inspect_accuracy_list) / document_pages
