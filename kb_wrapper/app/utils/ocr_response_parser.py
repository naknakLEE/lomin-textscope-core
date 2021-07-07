from typing import Any, List
from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.errors import exceptions as ex
from kb_wrapper.app import models


settings = get_settings()
parameter_error_set = settings.PARAMETER_ERROR_SET
kv_type_set = settings.KV_TYPE_SET


def check_item_included(kv, items) -> bool:
    for item in items:
        if item in kv:
            return True
    return False


def set_ocr_response(ocr_results: models.ResponseHandlerParameter, doc_types: List) -> Any:
    for ocr_result, doc_type in zip(ocr_results, doc_types):
        for ocr_result in "kv":
            ocr_result["kv"] = getattr(models, doc_type)(**ocr_result["kv"])
    return ocr_results


# args: models.ResponseHandlerParameter
def response_handler(
    status_code: int,
    description: str = "",
    ocr_result: dict = {},
    msg: str = "",
    request_id: str = "",
    request_at: str = "",
    response_at: str = "",
    response_id: str = "",
    response_time: str = "",
    detail: str = "",
    status_code_code: str = "",
    exc: Exception = None,
    doc_type: List = "",
) -> dict:
    ocr_result = set_ocr_response(ocr_result, doc_type) if "kv" in ocr_result else ocr_result
    if status_code >= 1000 and status_code <= 1400:
        result = models.SuccessfulResponse(
            status_code=status_code,
            ocr_result=ocr_result,
            request_id=request_id,
            request_at=request_at,
            response_at=response_at,
            response_id=response_id,
            response_time=response_time,
        )
        "성공적인 인식 케이스"
    elif status_code in parameter_error_set.keys():
        result = models.ParameterError(
            code=status_code, error_message=parameter_error_set[status_code]
        )
        "파라미터 오류"
    elif status_code == 2400 or status_code == 500:
        result = ex.serverException()
        "엔진 서버 미응답"
    elif status_code == 3400:
        result = ex.inferenceResultException()
        "OCR 엔진 인식결과 이상"
    elif status_code == 4400:
        result = ex.serverTemplateException()
        "문서종류가 상이"
    elif status_code == 7400:
        result = ex.timeoutException(description=description)
        "Timeout 발생"
    elif status_code == 8400:
        result = ex.parameterException(description=msg)
        "Error Response"
    elif status_code == 9400:
        result = ex.otherException(description=description)
        "Error Response"
    elif status_code == 400:
        result = ex.otherException(description=description)
        "bad request"
    elif status_code == 403:
        result = ex.otherException(description=description)
        "forbidden"
    elif status_code == 404:
        result = ex.otherException(description=description)
        "not found"
    elif status_code == 502:
        result = ex.otherException(description=description)
        "bad gateway"
    elif status_code == 503:
        result = ex.otherException(description=description)
        "service unavailable"
    elif status_code >= 405 or status_code < 200:
        result = ex.otherException(description=description)
    return result.__dict__
