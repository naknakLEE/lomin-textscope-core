from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.errors import exceptions as ex
from kb_wrapper.app import models


settings = get_settings()
parameter_error_set = settings.PARAMETER_ERROR_SET
reverse_document_type_set = settings.reverse_document_type_set


def set_ocr_response(ocr_result: models.OcrResult):
    doc_type = ocr_result["doc_type"]
    if doc_type == "사업자등록증":
        ...
    elif doc_type == "고유번호증":
        ...
    elif doc_type == "통장사본":
        ...
    elif doc_type == "주민등록증" or doc_type == "재외국민등록증":
        ...
    elif doc_type == "운전면허증":
        ...
    elif doc_type == "외국인등록증" or doc_type == "외국국적동포거소신고증" or doc_type == "영주증":
        ...
    elif doc_type == "여권":
        ...
    elif doc_type == "법인등기사항전부증명서":
        ...
    elif doc_type == "인감증명서":
        ...


def response_handler(args: models.ResponseHandlerParameter):
    if args.status >= 1000 and args.status <= 1400:
        result = models.SuccessfulResponse(
            code=args.status,
            ocr_result=args.ocrResult,
            request_id=args.request_id,
            request_at=args.request_at,
            response_id=args.response_id,
            response_time=args.response_time,
        )
        "성공적인 인식 케이스"
    elif args.status in parameter_error_set.keys():
        result = models.ParameterError(
            code=args.status, error_message=parameter_error_set[args.status]
        )
        "파라미터 오류"
    elif args.status == 2400 or args.status == 500:
        result = ex.serverException()
        "엔진 서버 미응답"
    elif args.status == 3400:
        result = ex.inferenceResultException()
        "OCR 엔진 인식결과 이상"
    elif args.status == 4400:
        result = ex.serverTemplateException()
        "문서종류가 상이"
    elif args.status == 7400:
        result = ex.timeoutException(description=args.description)
        "Timeout 발생"
    elif args.status == 8400:
        result = ex.parameterException(description=args.msg)
        "Error Response"
    elif args.status == 9400:
        result = ex.otherException(description=args.description)
        "Error Response"
    elif args.status == 400:
        result = ex.otherException(description=args.description)
        "bad request"
    elif args.status == 403:
        result = ex.otherException(description=args.description)
        "forbidden"
    elif args.status == 404:
        result = ex.otherException(description=args.description)
        "not found"
    elif args.status == 502:
        result = ex.otherException(description=args.description)
        "bad gateway"
    elif args.status == 503:
        result = ex.otherException(description=args.description)
        "service unavailable"
    elif args.status >= 405 or args.status < 200:
        result = ex.otherException(description=args.description)
    return result.__dict__


# status: int,
# description: str = "",
# docuType: str = "",
# ocrResult: dict = {},
# msg: str = "",
# request_id: str = "",
# request_at: str = "",
# response_id: str = "",
# response_time: str = "",
# detail: str = "",
# status_code: str = "",
# exc: Exception = None,
