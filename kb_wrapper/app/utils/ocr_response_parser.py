from typing import Any
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


def set_ocr_response(ocr_result: models.ResponseHandlerParameter) -> Any:
    kv = ocr_result["kv"]
    for key, values in kv_type_set:
        if check_item_included(kv, values):
            kv_model = getattr(models, key)
            return kv_model(**kv)
    return None


# args: models.ResponseHandlerParameter
def response_handler(
    status: int,
    description: str = "",
    docuType: str = "",
    ocrResult: dict = {},
    msg: str = "",
    request_id: str = "",
    request_at: str = "",
    response_id: str = "",
    response_time: str = "",
    detail: str = "",
    status_code: str = "",
    exc: Exception = None,
) -> dict:
    if status >= 1000 and status <= 1400:
        result = models.SuccessfulResponse(
            code=status,
            ocr_result=set_ocr_response(ocrResult),
            request_id=request_id,
            request_at=request_at,
            response_id=response_id,
            response_time=response_time,
        )
        "성공적인 인식 케이스"
    elif status in parameter_error_set.keys():
        result = models.ParameterError(code=status, error_message=parameter_error_set[status])
        "파라미터 오류"
    elif status == 2400 or status == 500:
        result = ex.serverException()
        "엔진 서버 미응답"
    elif status == 3400:
        result = ex.inferenceResultException()
        "OCR 엔진 인식결과 이상"
    elif status == 4400:
        result = ex.serverTemplateException()
        "문서종류가 상이"
    elif status == 7400:
        result = ex.timeoutException(description=description)
        "Timeout 발생"
    elif status == 8400:
        result = ex.parameterException(description=msg)
        "Error Response"
    elif status == 9400:
        result = ex.otherException(description=description)
        "Error Response"
    elif status == 400:
        result = ex.otherException(description=description)
        "bad request"
    elif status == 403:
        result = ex.otherException(description=description)
        "forbidden"
    elif status == 404:
        result = ex.otherException(description=description)
        "not found"
    elif status == 502:
        result = ex.otherException(description=description)
        "bad gateway"
    elif status == 503:
        result = ex.otherException(description=description)
        "service unavailable"
    elif status >= 405 or status < 200:
        result = ex.otherException(description=description)
    return result.__dict__
