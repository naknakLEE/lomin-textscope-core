import sys
sys.path.append("pp_server")
import copy

from pp_server.pp.business.kbl1 import postprocess_kbl1_md_prs

input = {
    "MD-DCC":{
        "type":"word",
        "value":[
            "J304",
            "JOO ;"
        ],
        "box":[[0, 0, 0, 0], [0, 0, 0, 0],],
        "score":0.1,
        "class":"MD-DCC",
        "text":[
            "J304",
            "JOO ;"
        ]
    }
}

predict = {
    "MD-DCC":{
        "type":"word",
        "value":[
            "J304",
            "J00"
        ],
        "box":[[0, 0, 0, 0], [0, 0, 0, 0]],
        "score":0.1,
        "class":"MD-DCC",
        "text":[
            "J304",
            "J00"
        ]
    },
    "MD-PC":{
        "type":"word",
        "text":"",
        "value":"",
        "score":0,
        "class":"MD-PC",
        "box":[
            0,
            0,
            0,
            0
        ],
        "merged_count":1
    }
    }

def test_MD_DCC_second_word_after_must_number():
    """
        TEST1: 두번째 문자 이후는 숫자로만 이루어져야된다.
        TEST2: 특수문자는 없어야된다.
    """
    assert postprocess_kbl1_md_prs(
        kv = input, 
        kv_with_header = [], 
        kv_without_header = [], 
        list_of_string = []
        ) == predict

