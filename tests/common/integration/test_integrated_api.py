from os import path
from typing import List, Any, Optional, Dict
from tests.common.utils.const import Const
from tests.common.utils.util import *

import json

import uuid
import requests
import pytest

constants = Const()
_root_url=constants.INTEGRATED_API_ROOT_URL
_sample_image_dir=path.join(constants.PROJECT_ROOT_PATH, constants.SAMPLE_IMAGE_PATH)
res_format_full_path = path.join(constants.PROJECT_ROOT_PATH, constants.RESPONSE_FORMAT_PATH)
f = open(res_format_full_path, 'r')
_format_json = json.load(f)

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
    url = _root_url + url_path
    token = None

    try:
        with open(_sample_image_dir, "rb") as f:
            response = requests.post(url,headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},files={"file": f})
    except Exception as e:
        print(e)
    # return document_id

    # response normal
    assert 200 == response.status_code, "/api/v1/docx 응답 코드가 \"200\"과 일치하지 않습니다."
    docx_response_json=response.json()
    print(convert_dict_value_to_none(docx_response_json))
    print(_format_json["post_api_v1_docx"])
    ## format
    assert convert_dict_value_to_none(docx_response_json) == _format_json["post_api_v1_docx"], "/api/v1/docx 응답 구조가 일치하지 않습니다."

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
    url = f"{_root_url}/api/v1/inference/kv"
    # token = post_auth_token()
    token = None
    document_id = post_upload_file(
        _sample_image_dir, token)
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
    print(_format_json["post_api_v1_inference_kv"])
    ## format
    assert convert_dict_value_to_none(kv_response_json) == _format_json["post_api_v1_inference_kv"], "/api/v1/inference/kv 응답 구조가 일치하지 않습니다."
    
    ## content