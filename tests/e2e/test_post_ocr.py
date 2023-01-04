
import pytest
import json
import requests
import time
import os

def test_post_ocr_request(post_ocr_args):
    """
        [POST] /nak/inference/ocr Test
        실제 해당경로에 파일이 만들어지는것까지 Test
    """
    request_body = {
        "document_dir": post_ocr_args['document_dir'],
        "rectify": {
            "rotation_90n": True,
            "rotation_fine": True
        },
        "detection_score_threshold": 0.3,
        "use_text_extraction": False,
        "detection_resize_ratio": 1,
        "pdf_file_name": post_ocr_args['pdf_file_name']
        }    

    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }
    
    res = requests.post(
        url='http://localhost:8090/nak/inference/ocr',
        headers=headers,
        data=json.dumps(request_body),
    )
    
    assert res.status_code == 200
    
    time.sleep(30)
    
    assert os.path.isfile(post_ocr_args['pdf_file_name']) == True
    