
'''
inference 시 필요한 각종 util logic
'''

def get_removed_text_inference_result(inference_result : dict, post_processing_type: str):
    '''
    inference_result에서 인식된 텍스트만 삭제하여 return 합니다(개인정보 보호이슈).
    '''
    # text 삭제 
    inference_result.update(texts=[])
    
    # kv 내 value 삭제
    if 'kv' in inference_result.keys() or post_processing_type in ["kv"]:
        inference_result.update(kv = remove_kv_value(inference_result["kv"]))

    # table 내 content 삭제
    if 'tables' in inference_result.keys() and len(inference_result['tables']) > 0:
        inference_result.update(tables = remove_table_value(inference_result['tables'][0]))
    # if inference_result 
    return inference_result

def remove_kv_value(kv: dict):
    '''
    inference_result의 kv에서 text,value 값들을 공백으로 치환하여 return 합니다. 
    '''
    if 'doc_type' not in kv.keys():
        for key in kv.keys():
            kv[key].update(value = "", text = "")

    return kv

def remove_table_value(table: dict):
    '''
    inference_result의 table/body/content에서 text 값들을 공백으로 치환하여 return 합니다. 
    '''
    try:
        for index, key in enumerate(table['body']['content']):
            table['body']['content'][index] = list(map(lambda x:0, key))
    except:
        return table
    return table

def judge_use_hint(inputs: dict):
    route = inputs.get("route_name")
    
    if route == None: 
        return False
    elif route == "cls_kv" and inputs.get("kv") is not None:
        hint= inputs["kv"].get("hint") 
        return hint is not None and hint.get("doc_type") is not None and hint.get("doc_type")["use"] == True and hint.get("doc_type")["trust"] == True
    elif route == "kv" and inputs.get("hint") is not None:
        hint= inputs.get("hint") 
        return hint.get("doc_type") is not None and hint.get("doc_type")["use"] == True and hint.get("doc_type")["trust"] == True
    else:
        return False
