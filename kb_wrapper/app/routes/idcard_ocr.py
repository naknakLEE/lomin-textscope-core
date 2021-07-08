import httpx
import requests
import cv2
import time
import numpy as np
import os
import sys
import traceback

from datetime import datetime
from pytz import timezone
from typing import Any, List
from fastapi import Request, APIRouter, Form, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from loguru import logger

from kb_wrapper.app import models
from kb_wrapper.app.errors import exceptions as ex
from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.utils.request_parser import parse_multi_form
from kb_wrapper.app.utils.ocr_result_parser import parse_kakaobank
from kb_wrapper.app.utils.ocr_response_parser import response_handler


router = APIRouter()
settings = get_settings()
doc_type_set = settings.DOCUMENT_TYPE_SET
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


DOC_TYPE_SET = {
    # 운전면허증 + 주민등록증, 우선 랜덤으로 추출할까?
    "REGISTRATION_SET_KEY": [
        "L1",
        "L3",
        "R6",
        "W2",
    ],
    # 외국인등록증 + 외국국적동포거소신고증 +영주증
    "FOREIGNER_SET_KEY": ["J6"],
    # 여권
    "PASSPORT_KEY": ["J5"],
}


DOC_KEY_SET = {
    "REGISTRATION_SET_KEY": [
        "rrc_title",
        "rrc_name",
        "rrc_regnum",
        "rrc_issue_date",
    ],
    "DRIVER_LICENSE_KEY": [
        "dlc_title",
        "dlc_name",
        "dlc_regnum",
        "dlc_issue_date",
        "dlc_license_num",
        "dlc_exp_date",
    ],
    "FOREIGNER_SET_KEY": [
        "arc_title",
        "arc_name",
        "arc_regnum",
        "arc_issue_date",
    ],
    "PASSPORT_KEY": [
        "pp_title",
        "pp_name",
        "pp_regnum",
        "pp_issue_date",
    ],
    "BusinessRegistration": [
        "cbr_regnum_business"
        "cbr_regnum_corp"
        "cbr_name"
        "cbr_address_business"
        "cbr_address_headquarter"
        "cbr_work_type"
        "cbr_work_cond"
    ],
    "UniqueNumber": ["cun_regnum_business" "cun_name" "cun_address_business"],
    "CopyOfPassbook": ["bb_account_num" "bb_account_holder" "bb_bank"],
    "ResidentRegistrationCardAndOverseasNationalRegistrationCard": [
        "rrc_title" "rrc_name" "rrc_regnum" "rrc_issue_date"
    ],
    "DriverLicense": [
        "dlc_title" "dlc_name" "dlc_regnum" "dlc_issue_date" "dlc_license_num" "dlc_exp_date"
    ],
    "AlienRegistrationCardAndForeignNationalityResidenceReportAndPermanentResidenceCard": [
        "arc_title" "arc_name" "arc_regnum" "arc_issue_date"
    ],
    "Passport": ["pp_title" "pp_name" "pp_regnum" "pp_issue_date"],
    "CertificateOfAllCorporateRegistrationDetails": [
        "ccr_title" "ccr_issue_date" "ccr_num_pages" "ccr_issued_stock"
    ],
    "SealCertificate": ["crs_issue_date"],
}


@router.get("/status")
async def check_status() -> JSONResponse:
    """
    - 서비스의 상태를 모니터링합니다.
    - Textscope API가 정상적으로 작동하고 있는 경우 200 status code와 함께 "on working" 메세지를 반환합니다.
    """
    try:
        serving_server_status_check_url = (
            f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/healthz"
        )
        response = requests.get(serving_server_status_check_url)
        assert response.status_code == 200
        is_serving_server_working = "True"
    except Exception:
        is_serving_server_working = "False"

    return JSONResponse(content=jsonable_encoder({"message": "onwroking"}))
    status = f"is_serving_server_working: {is_serving_server_working}"
    return JSONResponse(f"Textscope API ({status})")


@router.put("/upload")
async def upload_data(file: UploadFile = File(...)) -> Any:
    """
    - 개발시 원격으로 로민 API를 호출할 때 파일을 업로드합니다. 고객사의 운영환경 서버에는 파일이 이미 존재하겠지만 테스트시에는 직접 준비해야 하므로, 이 API는 개발시에 파일이 존재하도록 만들어주는 역할을 합니다.
    - 파일 업로드 경로는 미리 협의된 위치에 된다고 가정합니다. 개발시에는 컨테이너 내부 경로 /textscope/upload 라고 가정하겠습니다.
    """

    byte_image_data = await file.read()
    encoded_img = np.frombuffer(byte_image_data, dtype=np.uint8)
    image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
    current_time = time.time()
    cv2.imwrite(f"/textscope/upload/{current_time}.jpg", image)
    return JSONResponse(content=jsonable_encoder({"message": "File upload successful"}))
    return JSONResponse(content=jsonable_encoder({"message": "File upload failes"}))


@router.post("/ocr/all")
async def upload_data(
    request_id: str = Form(...),
    image_path: str = Form(...),
    page: str = Form(...),
) -> Any:
    """
    - /ocr/kv 요청에서 원하는 값을 얻지 못한 경우 /ocr/all 경로로 추가인식 요청을 통해 전문을 인식할 수 있습니다.
    - request_id, image_path는 /ocr/kv 요청과 동일합니다.
    - /ocr/all 요청은 문서의 전체 페이지가 아니라 특정 페이지만을 인식하는 것을 가정합니다. page 값은 어떤 페이지를 인식할지 정의합니다.
    """

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": "None",
        "page": page,
    }

    if not os.path.isfile(image_path):
        return JSONResponse(
            content={
                "status_code": "2100",
                "error_message": "이미지 파일이 경로에 존재하지 않음",
            }
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TEXTSCOPE_SERVER_URL}/v1/inference/tiff/idcard",
                data=data,
                timeout=300.0,
            )
            result = response.json()
            logger.debug(f"result check: {result}")
            result.update(result["ocr_result"])
            result["status_code"] = int(result["code"])
            inference_result = list()
            for box, score, text in zip(result["boxes"], result["scores"], result["texts"]):
                inference_result.append(
                    {
                        "bbox": box,
                        "scores": score,  # 왜 scores인지?
                        "text": text,
                    }
                )
            result["result"] = inference_result
            del result["code"], result["ocr_result"]
            return models.GeneralOcrResponse(**result)
        except:
            logger.debug(f"Unexpected error: {sys.exc_info()}")
            logger.debug(traceback.print_exc())
            return JSONResponse(
                content=jsonable_encoder(
                    {
                        "status_code": "3000",
                        "error_message": "알 수 없는 서버 내부 에러 발생",
                    }
                )
            )

    # return JSONResponse(status_code=200, content=jsonable_encoder(result))


def get_doc_type_using_doc_code(values: dict, doc_code: str):
    # inference 결과로 doc_key_set 못찾으면 doc_code를 이용해 탐색
    if "dlc_license_num" in values["kv"]:
        return DOC_KEY_SET["DRIVER_LICENSE_KEY"]
    for key, values in DOC_TYPE_SET.items():
        if doc_code in values:
            return DOC_KEY_SET[key]
    return None


def set_kv_schmea_according_to_doc_type(values: dict, doc_key: str) -> dict:
    doc_keys = get_doc_type_using_doc_code(values, doc_key)
    # below 2 line enable if not set all doc_type in doc_key_set
    if doc_keys is None:
        doc_keys = DOC_KEY_SET["REGISTRATION_SET_KEY"]
    prefix = "".join([doc_keys[0].split("_")[0], "_"])
    prefix_len = len(prefix)
    for key in doc_keys:
        if key[prefix_len:] in values["kv"] or key in values["kv"]:
            if key in values["kv"]:
                values["kv"][key] = values["kv"].pop(key)
            elif key not in values["kv"]:
                values["kv"][key] = values["kv"].pop(key[prefix_len:])
        else:
            values["kv"][key] = ""
    return values


def set_kv_values(ocr_result: dict) -> dict:
    for values in ocr_result.values():
        if len(values) <= 1:
            continue
        if "expiration_date" in values:
            values["exp_data"] = values.pop("expiration_date")
        values["regnum"] = values.pop("id")
        values["kv"] = {
            "name": values["name"],
            "regnum": values["regnum"],
            "issue_date": values["issue_date"],
        }
        if "expiration_date" in values:
            values["kv"]["expiration_date"] = values["expiration_date"]
        if "dlc_license_num" in values:
            values["kv"]["dlc_license_num"] = values["dlc_license_num"]

    return ocr_result


def postprocess_ocr_results(ocr_result: dict) -> List:
    ocr_result = set_kv_values(ocr_result)
    response_ocr_results = list()
    for i, result in enumerate(ocr_result.values()):
        page = str(i + 1)
        status_code = 100 if len(result) > 1 else 400
        doc_type = doc_type_set[result["doc_type"]]
        response_ocr_result = {"page": page, "status_code": status_code, "doc_type": doc_type}
        if "kv" in result:
            if "name" in result["kv"]:
                result = set_kv_schmea_according_to_doc_type(result, result["doc_type"])
            response_ocr_result["kv"] = result["kv"]
        response_ocr_results.append(response_ocr_result)
    return response_ocr_results


@router.post("/ocr/kv")
async def inference(
    image_path: str = Form(...),
    request_id: str = Form(...),
    doc_type=Form(...),
) -> Any:
    """
    - 멀티페이지 tiff 이미지의 모든 페이지에 대하여 주요 정보(key-value)를 추출합니다.
    - `request_id`는 모든 개별 요청이 갖는 unique한 값입니다. 각각의 요청이 항상 서로 다른 request_id를 가지게 하도록 하기 위하여 이 값에는 요청시의 timestamp, 파일의 체크섬 등이 포함될 수 있습니다.
    - `image_path`는 인식 대상 문서가 저장된 절대경로입니다.
    - doc_type은 전문으로부터 확인된 각 페이지별 문서 종류입니다. Array로 주어지는 이 값의 요소들은 문서 종류별로 정의된 코드 값입니다.
    """

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": doc_type,
        "page": "None",
    }

    if not os.path.isfile(image_path):
        return JSONResponse(
            content={
                "status_code": "2100",
                "error_message": "이미지 파일이 경로에 존재하지 않음",
            }
        )

    request_at = datetime.now(timezone("Asia/Seoul"))
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TEXTSCOPE_SERVER_URL}/v1/inference/tiff/idcard",
                data=data,
                timeout=300.0,
            )
            response_at = datetime.now(timezone("Asia/Seoul"))
            result = response.json()
            result["request_at"] = " ".join([request_at.strftime("%Y-%m-%d %H:%M:%S"), "KST"])
            result["response_at"] = " ".join([response_at.strftime("%Y-%m-%d %H:%M:%S"), "KST"])
            result["response_time"] = str((response_at - request_at).total_seconds())
            result["request_id"] = request_id
            result["ocr_result"] = postprocess_ocr_results(result["ocr_result"])
            result["status_code"] = int(result["code"])
            del result["code"]
            return response_handler(**result)
        except:
            logger.debug(f"Unexpected error: {sys.exc_info()}")
            logger.debug(traceback.print_exc())

            return JSONResponse(
                content=jsonable_encoder(
                    {
                        "status_code": "3000",
                        "error_message": "알 수 없는 서버 내부 에러 발생",
                    }
                )
            )
        return JSONResponse(status_code=200, content=jsonable_encoder(result))
