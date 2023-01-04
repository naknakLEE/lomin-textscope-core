
import pytest
import requests
import json

def test_put_pdf(put_pdf_arg):
    """
        [POST] /nak/inference/ocr Test
        실제 해당경로에 파일이 만들어지는것까지 Test
    """
    request_body = {
        "pdf_dir": put_pdf_arg['pdf_dir'],
        }    

    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }
    
    res = requests.put(
        url='http://localhost:8090/nak/pdf',
        headers=headers,
        data=json.dumps(request_body),
    )
    
    assert res.status_code == 200
    
    