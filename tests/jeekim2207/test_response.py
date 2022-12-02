import requests
import json
import uuid

from typing import List, Any, Optional, Dict
from tests.jeekim2207.utils import post_auth_token, post_upload_file

inf_kv_rseponse_structure = {
    "request": {
        "document_id": None,
        "detection_score_threshold": None,
        "rectify": {
            "rotation_90n": None,
            "rotation_fine": None
        },
        "hint": {
            "key_value": [
                {
                    "use": None,
                    "trust": None,
                    "key": None,
                    "value": None
                }
            ],
            "doc_type": {
                "use": None,
                "trust": None,
                "doc_type": None
            }
        },
        "detection_resize_ratio": None,
        "page": None
    },
    "response_metadata": {
        "request_datetime": None,
        "response_datetime": None,
        "time_elapsed": None
    },
    "document_metadata": {
        "user_email": None,
        "filename": None,
        "document_model_type": None,
        "document_description": None,
        "pages": None,
        "upload_datetime": None
    },
    "resource_id": {},
    "prediction": {
        "rectification": {
            "rotated": None,
            "expand": None,
            "image": {
                "width": None,
                "height": None
            }
        },
        "doc_type": {
            "doc_type_code": None,
            "doc_type_name_kr": None,
            "doc_type_name_en": None,
            "confidence": None,
            "is_hint_used": None,
            "is_hint_trusted": None
        },
        "key_values": [
            {
                "id": None,
                "type": None,
                "key": None,
                "confidence": None,
                "text_ids": None,
                "value": None,
                "bbox": {
                    "x": None,
                    "y": None,
                    "w": None,
                    "h": None
                },
                "comparison": None,
                "is_hint_used": None,
                "is_hint_trusted": None
            }
        ],
        "texts": [
            {
                "id": None,
                "text": None,
                "bbox": {
                    "x": None,
                    "y": None,
                    "w": None,
                    "h": None
                },
                "confidence": None,
                "kv_ids": None
            }
        ],
        "tables": [
            {
                "shape": None,
                "column-header": {
                    "bbox": None,
                    "content": None,
                    "score": None,
                    "position": None,
                    "span": None,
                    "key_code": None
                },
                "body": {
                    "bbox": None,
                    "content": None,
                    "score": None,
                    "position": None,
                    "span": None
                },
                "is_big_table": None
            }
        ]
    }
}


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
            

def test_MD_PRS_response_200_and_structure():
    url = "http://localhost:8090/api/v1/inference/kv"
    token = post_auth_token()
    document_id = post_upload_file(
        "tests/jeekim2207/image_MD-PRS_hklife_1000_all_000008.png", token)
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
                    "key": "FN-BB-BID",
                    "value": "2018.05.01"
                }
            ],
            "doc_type": {
                "use": True,
                "trust": True,
                "doc_type": "MD-PRS"
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
    response = requests.request("POST", url, headers=headers,
                                data=json.dumps(request_input))
    assert convert_dict_value_to_none(response.json()) == inf_kv_rseponse_structure, "/api/v1/inference/kv 응답 구조가 일치하지 않습니다."
