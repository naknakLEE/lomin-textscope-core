from typing import List, Any, Optional, Dict

from os import path

import json

import uuid
import requests
import pytest

ROOT_URL="http://localhost:8050"
RESPONSE_FORMAT_PATH = path.join(path.dirname(path.realpath(__file__)), "assets/format/response_format.json")
f = open(RESPONSE_FORMAT_PATH, 'r')
FORMAT_JSON = json.load(f)


### test cls_kv api
@pytest.mark.asyncio("Test 'POST /api/v1/inference/cls-kv api")
async def test_post_api_v1_inference_cls_kv():
    """
        POST api/v1/inference/cls-kv API가
            1. 정상적으로 처리(200)되는지
            2. 응답 구조가 일치하는지 확인합니다..
    
        Value는 None으로 변환하고 Key만 확인합니다.
        List인 경우 첫번째 요소만 확인합니다.
    """
    url = f"{ROOT_URL}/api/v1/inference/cls-kv"
    # token = post_auth_token()
    token = None
    document_id = post_upload_file(
        "assets/images/MD-CAD/22032600000301_입퇴원확인서_2022032608171891.png", token)
    # print(document_id)
    request_input = {
        "document_id": document_id,
        "rectify": {
            "rotation_90n": True,
            "rotation_fine": True
        },
        "cls": {
            "cls_threshold": 0.6
        },
        "kv": {
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
                    "use": False,
                    "trust": False,
                    "doc_type": "LINA1-09"
                }
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
    assert 200 == response.status_code, "/api/v1/inference/cls-kv 응답 코드가 \"200\"과 일치하지 않습니다."
    cls_kv_response_json=response.json()
    # print(convert_dict_value_to_none(x))
    # print(inf_cls_kv_response_structure)
    
    ## format
    assert convert_dict_value_to_none(cls_kv_response_json) == FORMAT_JSON["post_api_v1_inference_cls_kv"], "/api/v1/inference/cls-kv 응답 구조가 일치하지 않습니다."
    
    ## content