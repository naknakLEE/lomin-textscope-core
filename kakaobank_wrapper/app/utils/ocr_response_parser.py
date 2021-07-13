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
):
    if status == 1200:
        result = ex.minQltException(
            minQlt=minQlt,
            reliability=reliability,
            docuType=docuType,
            ocrResult=ocrResult,
        )
    elif status == 1400:
        result = ex.minQltException(minQlt=minQlt)
        "최소퀄리티 미달"
    elif status == 2400 or status == 500:
        result = ex.serverException(minQlt=minQlt)
        "엔진 서버 미응답"
    elif status == 3400:
        result = ex.inferenceResultException(minQlt=minQlt)
        "OCR 엔진 인식결과 이상"
    elif status == 4400:
        result = ex.serverTemplateException(minQlt=minQlt)
        "문서종류가 상이"
    elif status == 5400:
        result = ex.inferenceReliabilityException(minQlt=minQlt, reliability=reliability)
        "인식결과 신뢰도 낮음"
    elif status == 6400:
        result = ex.ocrResultEmptyException(minQlt=minQlt, reliability=reliability)
        "등기필증 인식 실패"
    elif status == 7400:
        result = ex.timeoutException(minQlt=minQlt, description=description)
        "Timeout 발생"
    elif status == 8400:
        result = ex.parameterException(minQlt=minQlt, description=msg)
        "Error Response"
    elif status == 9400:
        result = ex.otherException(minQlt=minQlt, description=description)
        "Error Response"
    elif status >= 405 or status < 200:
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 400:
        result = ex.otherException(minQlt=minQlt, description=description)
        "bad request"
    elif status == 403:
        result = ex.otherException(minQlt=minQlt, description=description)
        "forbidden"
    elif status == 404:
        result = ex.otherException(minQlt=minQlt, description=description)
        "not found"
    elif status == 502:
        result = ex.otherException(minQlt=minQlt, description=description)
        "bad gateway"
    elif status == 503:
        result = ex.otherException(minQlt=minQlt, description=description)
        "service unavailable"
    return vars(result)
