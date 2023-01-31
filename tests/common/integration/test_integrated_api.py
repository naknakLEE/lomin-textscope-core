from os import path
from typing import List, Any, Optional, Dict
from tests.common.utils.const import Const
from tests.common.utils import util

import json

import uuid
import requests
import pytest

constants = Const()

ROOT_URL=constants.INTEGRATED_API_ROOT_URL
res_format_full_path = path.join(path.dirname(path.realpath(__file__)), "../../../", constants.RESPONSE_FORMAT_PATH)
f = open(res_format_full_path, 'r')
FORMAT_JSON = json.load(f)

# reqeust post upload file
def post_upload_file(file_path: str, token: str):
    url_path = "/api/v1/docx"
    url = ROOT_URL + url_path
    
    document_id = None
    with open(file_path, "rb") as f:
        response = requests.post(url,headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},files={"file": f},)
        
        if response.status_code == 200:
            document_id = response.json().get("document_id")
        else:
            print(f"request error: {response.status_code} {response.json()}")

    return document_id

def convert_list_value_to_none(inf_response: List[Any]) -> Optional[List[Any]]:
    if len(inf_response) == 0:
        return None

    first_of_list = inf_response[0]
    
    if isinstance(first_of_list, dict):
        none_dict = convert_dict_value_to_none(first_of_list)
    else:
        return None
    return [none_dict]
    

def convert_dict_value_to_none(inf_response: Dict[str, Any]) -> Dict[str, Any]:
    include_keys = ['key_value', 'key_values', 'texts', 'tables', 'span', 'key_code']
    for key, value in inf_response.items():
        if isinstance(value, dict):
            inf_response[key] = convert_dict_value_to_none(value)
        elif isinstance(value, list) and key in include_keys:
            inf_response[key] = convert_list_value_to_none(value)
        else:
            inf_response[key] = None
    return inf_response
            

@pytest.mark.asyncio("Test 'POST /api/v1/docx api")
async def test_post_api_v1_docx():
    """
        POST api/v1/docx API가
            1. 정상적으로 처리(200)되는지
            2. 응답 구조가 일치하는지 확인합니다.
    
        Value는 None으로 변환하고 Key만 확인합니다.
        List인 경우 첫번째 요소만 확인합니다.
    """
    url_path = "/api/v1/docx"
    url = ROOT_URL + url_path
    token = None

    try:
        with open("../assets/images/MD-CAD/22032600000301_입퇴원확인서_2022032608171891.png", "rb") as f:
            response = requests.post(url,headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},files={"file": f})
    except Exception as e:
        print(e)
    # return document_id

    # response normal
    assert 200 == response.status_code, "/api/v1/docx 응답 코드가 \"200\"과 일치하지 않습니다."
    docx_response_json=response.json()
    print(convert_dict_value_to_none(docx_response_json))
    print(FORMAT_JSON["post_api_v1_docx"])
    ## format
    assert convert_dict_value_to_none(docx_response_json) == FORMAT_JSON["post_api_v1_docx"], "/api/v1/docx 응답 구조가 일치하지 않습니다."

### test cls_kv api
@pytest.mark.asyncio("Test 'POST /api/v1/inference/kv api")
async def test_post_api_v1_inference_kv():
    """
        POST api/v1/inference/cls-kv API가
            1. 정상적으로 처리(200)되는지
            2. 응답 구조가 일치하는지 확인합니다..
    
        Value는 None으로 변환하고 Key만 확인합니다.
        List인 경우 첫번째 요소만 확인합니다.
    """
    url = f"{ROOT_URL}/api/v1/inference/kv"
    # token = post_auth_token()
    token = None
    document_id = post_upload_file(
        "../assets/images/MD-CAD/22032600000301_입퇴원확인서_2022032608171891.png", token)
    # print(document_id)
    request_input = {
        "document_id": document_id,
        "rectify": {
            "rotation_90n": True,
            "rotation_fine": True
        },
        "hint": {
            "key_value": [
                {
                    "use": False,
                    "trust": False,
                    "key": "MD-CS",
                    "value": "2022.10.20"
                }
            ],
            "doc_type": {
                "use": True,
                "trust": True,
                "doc_type": "LINA1-09"
            }
        },
        "detection_score_threshold": 0.5,
        "detection_resize_ratio": 1,
        "page": 1
    }

    headers = {
        'x-request-id': str(uuid.uuid4()),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(request_input))
    
    # response normal
    assert 200 == response.status_code, "/api/v1/inference/kv 응답 코드가 \"200\"과 일치하지 않습니다."
    kv_response_json=response.json()
    # print(convert_dict_value_to_none(x))
    # print(inf_cls_kv_response_structure)
    print( convert_dict_value_to_none(kv_response_json))
    print(FORMAT_JSON["post_api_v1_inference_kv"])
    ## format
    assert convert_dict_value_to_none(kv_response_json) == FORMAT_JSON["post_api_v1_inference_kv"], "/api/v1/inference/kv 응답 구조가 일치하지 않습니다."
    
    ## content