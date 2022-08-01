from sqlalchemy.orm import Session
from app.utils.postprocess import add_unrecognition_kv
from app.utils.postprocess import modif_class_code, del_class_code


def get_inspect_accuracy(session: Session, select_inference_result: dict, inspect_result: dict):
    # 인식 되지 않은 class None값으로 추가
    
    # TODO DB 이후 inference_result 수정이 되어 input이 DB inference_result 값과 달라짐
    # input값과 db의 inference_result값이 같다면 사용안해도 됨.
    del_class_code(select_inference_result)
    if select_inference_result.inference_result.get("doc_type", "NONE") in ["FN-OIP", "FN-BP"]:
        modif_class_code(select_inference_result)
    
    
    inference_kv = select_inference_result.inference_result.get("kv")
    inference_kv_count = len(inference_kv)
    _, unrecognition_kv = add_unrecognition_kv(session, select_inference_result)
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