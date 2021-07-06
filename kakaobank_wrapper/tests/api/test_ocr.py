import cv2

from typing import Dict
from fastapi.testclient import TestClient

from kakaobank_wrapper.app.common.const import get_settings


settings = get_settings()
KAKAO_WRAPPER_IP_ADDR = "182.20.0.22"
KAKAO_WRAPPER_IP_PORT = "8090"


def test_server_response(client: TestClient):
    image_dir = "./others/assets/family_cert.png"
    img = cv2.imread(image_dir)
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = img_encoded.tobytes()
    data = {"lnbzDocClcd": "D02", "lnbzMgntNo": "11111", "pwdNo": "1"}
    files = {
        "edmisId[0]": "1q2w3e4r",
        "edmisId[1]": "1a2s3d4f",
        "edmisId[2]": "1z2x3c4v",
        "imgFiles[0]": img_bytes,
        "imgFiles[1]": img_bytes,
        "imgFiles[2]": img_bytes,
    }
    response = client.post("api/v1/ocr", params=data, files=files, timeout=300.0)
    result = response.json()
    print("\033[96m" + f"{result}, {response.status_code}" + "\033[m")
    assert response.status_code == 200


def test_server_request(client: TestClient):
    image_dir = "./others/assets/family_cert.png"
    img = cv2.imread(image_dir)
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = img_encoded.tobytes()
    data = {"lnbzDocClcd": "D02", "lnbzMgntNo": "11111", "pwdNo": "1"}
    files = {
        "edmisId[1]": "1a2s3d4f",
        "edmisId[2]": "1z2x3c4v",
        "imgFiles[0]": img_bytes,
        "imgFiles[1]": img_bytes,
        "imgFiles[2]": img_bytes,
    }
    response = client.post("api/v1/ocr", params=data, files=files, timeout=300.0)
    result = response.json()
    print("\033[96m" + f"{result}, {response.status_code}" + "\033[m")
    assert response.status_code == 200


def test_required_parameter(client: TestClient):
    ...


def test_timeout(client: TestClient):
    ...


def test_authentication(client: TestClient):
    ...


def test_others(client: TestClient):
    ...
