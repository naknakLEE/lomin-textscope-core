import cv2
import time
import pytest
import asyncio

from typing import Dict, List
from loguru import logger
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi.applications import FastAPI

from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.errors import exceptions as ex
from kakaobank_wrapper.tests.utils.utils import (
    compare_dictionary_match,
    compare_dictionary_key_match,
)


settings = get_settings()
kakao_wrapper_ip_addr = settings.KAKAO_WRAPPER_IP_ADDR
kakao_wrapper_ip_port = settings.KAKAO_WRAPPER_IP_PORT
image_dir = f"{settings.BASE_PATH}/others/assets/family_cert.png"
kakaobank_wrapper_base_url = f"http://0.0.0.0:{kakao_wrapper_ip_port}"

with open(image_dir, "rb") as f:
    default_img_bytes = f.read()
random_int_number = int(time.time())
default_data = {"lnbzDocClcd": "D02", "lnbzMgntNo": random_int_number, "pwdNo": "1"}
default_files = {
    "edmisId[0]": f"{random_int_number*1}",
    "edmisId[1]": f"{random_int_number*2}",
    "edmisId[2]": f"{random_int_number*3}",
    "imgFiles[0]": default_img_bytes,
    "imgFiles[1]": default_img_bytes,
    "imgFiles[2]": default_img_bytes,
}


# 1200
def test_successful_response(client: TestClient):
    response = client.post("api/v1/ocr", params=default_data, files=default_files)
    results = response.json()
    logger.debug(f"results: {results}")
    assert type(results) == list
    assert response.status_code == 200
    for result in results:
        assert compare_dictionary_key_match(
            result,
            vars(
                ex.successful(
                    minQlt="dummy", reliability="dummy", docuType="dummy", ocrResult="dummy"
                )
            ),
        )


# 1400
# not implemented yet
def test_minQlt_error(client: TestClient):
    ...


# 2400
def test_ocr_server_no_response(client: TestClient):
    response = client.post("not_exist_url", params=default_data, files=default_files)
    result = response.json()
    logger.debug(result)
    assert response.status_code == 200
    assert compare_dictionary_match(result, vars(ex.serverException(minQlt="00")))


# 3400
# not implemented yet
def test_abnormal_ocr_results(client: TestClient):
    ...


# 4400
def test_request_params_pair_error(client: TestClient):
    data = {"lnbzDocClcd": "D02", "lnbzMgntNo": random_int_number, "pwdNo": "1"}
    files = {
        "edmisId[1]": f"{random_int_number*1}",
        "edmisId[2]": f"{random_int_number*2}",
        "imgFiles[0]": default_img_bytes,
        "imgFiles[1]": default_img_bytes,
        "imgFiles[2]": default_img_bytes,
    }
    response = client.post("api/v1/ocr", params=data, files=files)
    results = response.json()
    assert response.status_code == 200
    assert compare_dictionary_match(results, vars(ex.serverTemplateException(minQlt="00")))


# 4400
def test_request_form_error(client: TestClient):
    data = {"lnbzDocClcd_dummy": "D02", "lnMgngNo_dummy": random_int_number, "pwdNo_dummy": "1"}
    files = {
        "edmisId_dummy": f"random_int_number",
        "imgFiles_dummy": default_img_bytes,
    }
    params_value_error_response = client.post("api/v1/ocr", params=data, files=files)
    params_value_error_results = params_value_error_response.json()
    parameter_exception_dict = vars(
        ex.parameterException(minQlt="00", description="Required parameter not included")
    )
    assert params_value_error_response.status_code == 200
    assert compare_dictionary_match(params_value_error_results, parameter_exception_dict)


# 5400
# not implemented yet
def test_low_reliability_error(client: TestClient):
    ...


# 6400
def test_empty_all_field(client: TestClient):
    not_included_all_param_data = dict()
    not_included_all_files = dict()
    params_form_error_response = client.post(
        "api/v1/ocr", params=not_included_all_param_data, files=not_included_all_files
    )
    params_form_error_results = params_form_error_response.json()
    assert params_form_error_response.status_code == 200
    assert compare_dictionary_key_match(
        params_form_error_results,
        vars(ex.ocrResultEmptyException(minQlt="00", reliability="0.0")),
    )


@pytest.mark.asyncio
async def request(client):
    response = await client.post("api/v1/ocr", params=default_data, files=default_files)
    return response.json()


@pytest.mark.asyncio
async def task(count: int, app: FastAPI) -> List[Dict]:
    async with AsyncClient(app=app, base_url=kakaobank_wrapper_base_url) as client:
        tasks = [request(client) for _ in range(count)]
        results = await asyncio.gather(*tasks)
        logger.debug(f"Results: {results}")
        logger.debug(f"Results length: {len(results)}")
        return results


# 7400
@pytest.mark.asyncio
async def test_timeout_error(app: FastAPI):
    results = await task(count=5, app=app)
    timeout_error_count = 0
    for result in results:
        if result.get("status") == "7400":
            timeout_error_count += 1
    assert timeout_error_count > 0


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
    data = {"lnbzDocClcd": "D23", "lnbzMgntNo": random_int_number, "pwdNo": "1"}
    params_value_error_response = client.post("api/v1/ocr", params=data, files=default_files)
    params_value_error_results = params_value_error_response.json()
    parameter_exception_dict = vars(
        ex.parameterException(minQlt="00", description="lnbzDocClcd is not valid value")
    )
    assert params_value_error_response.status_code == 200
    logger.debug(f"params: {params_value_error_results}")
    assert params_value_error_results.get("status_code") == parameter_exception_dict.get("code")
    assert compare_dictionary_match(params_value_error_results, parameter_exception_dict)


# 8400
def test_D53_type_required_parameter_error(client: TestClient):
    data = {"lnbzDocClcd": "D53", "lnbzMgntNo": random_int_number}
    params_value_error_response = client.post("api/v1/ocr", params=data, files=default_files)
    params_value_error_results = params_value_error_response.json()
    parameter_exception_dict = vars(
        ex.parameterException(minQlt="00", description="D53 required parameter not included")
    )
    assert params_value_error_response.status_code == 200
    assert params_value_error_results.get("status_code") == parameter_exception_dict.get("code")
    assert compare_dictionary_match(params_value_error_results, parameter_exception_dict)


# 8400
def test_required_parameter_not_included_error(client: TestClient):
    not_included_some_param_data = {"lnbzMgntNo": random_int_number, "pwdNo": "1"}
    params_value_error_response = client.post(
        "api/v1/ocr", params=not_included_some_param_data, files=default_files
    )
    params_value_error_results = params_value_error_response.json()
    parameter_exception_dict = vars(
        ex.parameterException(minQlt="00", description="D53 required parameter not included")
    )
    logger.debug(f"check params: {params_value_error_results}")
    assert params_value_error_response.status_code == 200
    assert params_value_error_results.get("status_code") == parameter_exception_dict.get("code")
    assert compare_dictionary_match(params_value_error_results, parameter_exception_dict)


# 9400
# 발생할 가능성은?
def test_unexpected_error(client: TestClient):
    ...


# 8400
# 토큰을 같이 넣을까?
def test_authentication_error(client: TestClient):
    ...
