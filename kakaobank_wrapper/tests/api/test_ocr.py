import cv2

from typing import Dict
from fastapi.testclient import TestClient

from kakaobank_wrapper.app.common.const import get_settings


settings = get_settings()

MODEL_SERVER_URL = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"


def test_server_response(client: TestClient):
    image_dir = "./others/assets/000000000000000IMG_4825.jpg"
    img = cv2.imread(image_dir)
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = img_encoded.tobytes()
    files = {"image": ("documment_img.jpg", img_bytes)}
    response = client.post(f"{MODEL_SERVER_URL}/api/v1/ocr", files=files, timeout=300.0)
    result = response.json()
    assert result.status_code
    print("\033[96m" + f"{result}" + "\033[m")
    return result


def test_server_request(client: TestClient):
    ...


def test_required_parameter(client: TestClient):
    ...


def test_timeout(client: TestClient):
    ...


def test_authentication(client: TestClient):
    ...


def test_others(client: TestClient):
    ...
