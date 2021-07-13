from typing import Dict
from kakaobank_wrapper.app.errors import exceptions as ex


async def response_handler(
    status: int,
    minQlt: str = "",
    description: str = "",
    reliability: str = "",
    docuType: str = "",
    ocrResult: dict = {},
    msg: str = "",
    detail: str = "",
    status_code: str = "",
    exc: Exception = None,
) -> Dict:
    if status == 1200:
        result = ex.successful(
            minQlt=minQlt,
            reliability=reliability,
            docuType=docuType,
            ocrResult=ocrResult,
        )
    elif status == 1400:
        "최소퀄리티 미달"
        result = ex.minQltException(minQlt=minQlt)
    elif status == 2400 or status == 500:
        "엔진 서버 미응답"
        result = ex.serverException(minQlt=minQlt)
    elif status == 3400:
        "OCR 엔진 인식결과 이상"
        result = ex.inferenceResultException(minQlt=minQlt)
    elif status == 4400:
        "문서종류가 상이"
        result = ex.serverTemplateException(minQlt=minQlt)
    elif status == 5400:
        "인식결과 신뢰도 낮음"
        result = ex.inferenceReliabilityException(minQlt=minQlt, reliability=reliability)
    elif status == 6400:
        "등기필증 인식 실패"
        result = ex.ocrResultEmptyException(minQlt=minQlt, reliability=reliability)
    elif status == 7400:
        "Timeout 발생"
        result = ex.timeoutException(minQlt=minQlt, description=description)
    elif status == 8400:
        "Error Response"
        result = ex.parameterException(minQlt=minQlt, description=msg)
    elif status == 9400:
        "Error Response"
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status >= 405 or status < 200:
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 400:
        "bad request"
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 403:
        "forbidden"
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 404:
        "not found"
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 502:
        "bad gateway"
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 503:
        "service unavailable"
        result = ex.otherException(minQlt=minQlt, description=description)
    return vars(result)
