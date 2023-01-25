
from copy import deepcopy
from typing import List, Dict


'''
inference 시 필요한 각종 util logic
'''

def get_removed_text_inference_result(inference_result : dict):
    '''
    inference_result에서 인식된 텍스트만 삭제하여 return 합니다(개인정보 보호이슈).
    '''
    privacy_inference_result = deepcopy(inference_result)
    
    # text 삭제 
    privacy_inference_result.update(texts=[])
    
    # kv 내 value 삭제
    if 'kv' in privacy_inference_result.keys():
        __remove_kv_value__(privacy_inference_result["kv"])
    
    # table 내 content 삭제
    if 'tables' in privacy_inference_result.keys():
        __remove_table_value__(privacy_inference_result['tables'])
    
    
    return privacy_inference_result


def __remove_kv_value__(kv: Dict[str, dict]):
    '''
    inference_result의 kv에서 text,value 값들을 공백으로 치환하여 return 합니다. 
    '''
    if 'doc_type' in kv.keys(): return kv
    
    for k, v in kv.items():
        v.update(
            text="",
            value=""
        )
    
    
    return kv


def __remove_table_value__(tables: List[dict]):
    '''
    inference_result의 table/body/content에서 값들을 타입에 맞게 기본값으로 치환하여 return 합니다. 
    '''
    for table in tables:
        removed_body_content = list()
        for content in table.get("body", {}).get("content", []):
            removed_content = list()
            for v in content:
                if   isinstance(v, str):   removed_content.append("")
                elif isinstance(v, int):   removed_content.append(0)
                elif isinstance(v, float): removed_content.append(0.0)
            
            removed_body_content.append(removed_content)
        
        table["body"]["content"] = removed_body_content
    
    
    return table
