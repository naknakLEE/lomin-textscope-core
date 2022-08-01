from sqlalchemy.orm import Session
from app.utils.postprocess import add_unrecognition_kv
from app.database import schema


def get_inspect_accuracy(session: Session, select_inference_result: schema.InferenceInfo, inspect_result: dict):
    # 인식 되지 않은 class None값으로 추가
    
    select_inference_result, unrecognition_kv = add_unrecognition_kv(session, select_inference_result)
    inference_kv = select_inference_result.inference_result.get("kv")
    inference_kv_count = len(inference_kv)
    inspect_kv = inspect_result.get("kv")
    
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
    
    
    
    divide_parent = inference_kv_count + modify_count_unrecognition
    divide_child = divide_parent - (modify_count_unrecognition + modify_count_inference)
    inspect_accuracy = (divide_child / divide_parent) * 100
    return inspect_accuracy