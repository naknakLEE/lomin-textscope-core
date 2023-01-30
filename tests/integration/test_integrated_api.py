from typing import List, Any, Optional, Dict

import json
import uuid
import requests

ROOT_URL="http://localhost:8090"

inf_cls_kv_response_structure={
  "request": {
    "document_id": None,
    "detection_score_threshold": None,
    "rectify": {
      "rotation_90n": None,
      "rotation_fine": None
    },
    "cls": {
      "cls_threshold": None
    },
    "kv": {
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
    "doc_type": {
      "doc_type_code": None,
      "doc_type_name_kr": None,
      "doc_type_name_en": None,
      "confidence": None,
      "is_hint_used": None,
      "is_hint_trusted": None
    },
    "rectification": {
      "rotated": None,
      "expand": None,
      "image": {
        "width": None,
        "height": None
      }
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
    "tables":None,
    "texts":None,
    
    }
  }

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

# reqeust post upload file
def post_upload_file(file_path: str, token: str):
    url_path = "/api/v1/docx"
    url = ROOT_URL + url_path
    print(file_path)
    print(token)
    
    document_id = None
    with open(file_path, "rb") as f:
        response = requests.post(url,headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},files={"file": f},)
        
        print(response.status_code)
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
            

def test_cls_kv_response_200_and_structure():
    """
        api/v1/inference/kv API가 정상적으로 처리(200)되었을 때
        응답 구조가 일치하는지 확인합니다.
    
        Value는 None으로 변환하고 Key만 확인합니다.
        List인 경우 첫번째 요소만 확인합니다.
    """
    url = "http://localhost:8090/api/v1/inference/cls-kv"
    # token = post_auth_token()
    token = None
    document_id = post_upload_file(
        "assets/images/MD-CAD/22032600000301_입퇴원확인서_2022032608171891.png", token)
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

    print("document_id")
    print(document_id)
    headers = {
        'x-request-id': str(uuid.uuid4()),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(request_input))
    
    assert 200 == response.status_code
    x=response.json()
    # print(x)
    assert convert_dict_value_to_none(x) == inf_cls_kv_response_structure, "/api/v1/inference/cls-kv 응답 구조가 일치하지 않습니다."