import numpy as np

def get_diff_array_item_indexes(a: list, b: list):
    '''
    2개의 배열을 받아 다른 값을 가지고 있는 index를 배열에 담아 return 합니다.
    '''
    np_arr_a = np.array(a)
    np_arr_b = np.array(b)

    arr = np_arr_a == np_arr_b
    result = []
    for i, value in enumerate(arr):
        if not value:
            result.append(i)
    return result

def get_item_list_in_index(list: list, indexs: list):
    '''
    리스트를 받아서 index 배열 안에 있는 index의 item list를 return 합니다. 
    '''
    result = []
    for i in indexs:
        result.append(list[i])
    return result

def get_flatten_table_content(tables: list):
    '''
    tables를 받아 하위의 contents를 1차원 배열로 return 합니다.
    '''
    arr = (np.array(tables["body"]["content"])).flatten()
    return arr.tolist()

def get_inspect_accuracy(kv_list: list, el_list: list, kv_changed: list, el_changed: list):
    '''
    검수 정확도를 측정합니다. 정확도는 소수점 2자리까지 측정합니다. 

    정확도 = 100 - (변경된 kv+el 개수 / 전체 kv+el 개수  * 100)
    '''
    
    return round((100 - ((len(kv_changed) + len(el_changed)) / (len(kv_list) + len(el_list)) * 100)), 2)

def get_removed_changes_keyvalue(keyvalue: list):
    result = []

    for kv in keyvalue:
        kv['prediction'] = ""
        kv['corrected'] = ''
        result.append(kv)
        
    return result 