import cv2
import pytest

from typing import Dict
from fastapi.testclient import TestClient

from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.errors import exceptions as ex


settings = get_settings()
KAKAO_WRAPPER_IP_ADDR = "182.20.0.22"
KAKAO_WRAPPER_IP_PORT = "8090"
image_dir = "./others/assets/family_cert.png"
with open(image_dir, "rb") as f:
    default_img_bytes = f.read()
default_files = {
    "edmisId[0]": "1q2w3e4r",
    "edmisId[1]": "1a2s3d4f",
    "edmisId[2]": "1z2x3c4v",
    "imgFiles[0]": default_img_bytes,
    "imgFiles[1]": default_img_bytes,
    "imgFiles[2]": default_img_bytes,
}
default_data = {"lnbzDocClcd": "D02", "lnbzMgntNo": "11111", "pwdNo": "1"}

# 1200
def test_successful_response(client: TestClient):
    response = client.post("api/v1/ocr", params=default_data, files=default_files, timeout=30.0)
    result = response.json()
    print("\033[96m" + f"{result}, {response.status_code}" + "\033[m")
    assert response.status_code == 200


# 1400
# not implemented yet
def test_minQlt_error(client: TestClient):
    ...


# 2400
def test_ocr_server_no_response(client: TestClient):
    ...


# 3400
# not implemented yet
def test_abnormal_ocr_results(client: TestClient):
    ...


# 4400
def test_request_params_pair_error(client: TestClient):
    data = {"lnbzDocClcd": "D02", "lnbzMgntNo": "11111", "pwdNo": "1"}
    files = {
        "edmisId[1]": "1a2s3d4f",
        "edmisId[2]": "1z2x3c4v",
        "imgFiles[0]": default_img_bytes,
        "imgFiles[1]": default_img_bytes,
        "imgFiles[2]": default_img_bytes,
    }
    response = client.post("api/v1/ocr", params=data, files=files, timeout=30.0)
    results = response.json()
    assert results == ex.serverTemplateException(minQlt="00")


# 4400
# not implemented yet
def test_required_query_parameter_error(client: TestClient):
    not_included_some_param_data = {"lnbzMgntNo": "11111", "pwdNo": "1"}
    files = {
        "edmisId[0]": "1a2s3d4f",
        "imgFiles[0]": default_img_bytes,
    }
    params_form_error_response = client.post(
        "api/v1/ocr", params=not_included_some_param_data, files=files, timeout=30.0
    )
    params_form_error_results = params_form_error_response.json()
    assert params_form_error_results == ex.serverTemplateException(minQlt="00")


# 4400
# 잘못된 판단, 수정 필요
def test_required_query_parameters_error(client: TestClient):
    not_included_some_param_data = {"lnbzMgntNo": "11111", "pwdNo": "1"}
    files = {
        "edmisId[0]": "1a2s3d4f",
        "imgFiles[0]": default_img_bytes,
    }
    params_form_error_response = client.post(
        "api/v1/ocr", params=not_included_some_param_data, files=files, timeout=30.0
    )
    params_form_error_results = params_form_error_response.json()
    assert params_form_error_results == ex.serverTemplateException(minQlt="00")


# 5400
# not implemented yet
def test_low_reliability_error(client: TestClient):
    ...


# 6400
def test_empty_all_field(client: TestClient):
    ...


# 7400
def test_timeout_error(client: TestClient):
    ...


"""
• Parameter 오류
• description으로 상세설명 제공
    • 필수 파라미터가 안들어 온 경우
    • (등기필증 경우 필수파라미터 1개 더 많음
    • 문서 코드가 잘못된 경우
        • 등기필증(D54), 주민등록등본 (D01), 가족증명서(D02), 기본증명서 (D53) 중 하나가 아닌 경우
"""
# 8400
def test_not_valid_lnvzDocClcd_value_error(client: TestClient):
    data = {"lnbzDocClcd": "D23", "lnbzMgntNo": "11111", "pwdNo": "1"}
    params_value_error_response = client.post(
        "api/v1/ocr", params=data, files=default_files, timeout=30.0
    )

    params_value_error_results = params_value_error_response.json()
    assert params_value_error_results == ex.parameterException(
        minQlt="00", description="lnbzDocClcd is not valid value"
    )


# 8400
def test_D53_type_required_parameter_error(client: TestClient):
    data = {"lnbzDocClcd": "D54", "lnbzMgntNo": "11111"}
    params_value_error_response = client.post(
        "api/v1/ocr", params=data, files=default_files, timeout=30.0
    )
    params_value_error_results = params_value_error_response.json()
    assert params_value_error_results == ex.parameterException(
        minQlt="00", description="required parameter not included"
    )


# 8400
def test_required_parameter_not_included_error(client: TestClient):
    data = {"lnbzMgntNo": "11111"}
    params_value_error_response = client.post(
        "api/v1/ocr", params=data, files=default_files, timeout=30.0
    )
    params_value_error_results = params_value_error_response.json()
    assert params_value_error_results == ex.parameterException(
        minQlt="00", description="required parameter not included"
    )


# 9400
def test_unexpected_error(client: TestClient):
    ...


# 8400
def test_authentication_error(client: TestClient):
    ...
