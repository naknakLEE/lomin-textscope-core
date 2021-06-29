async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error


class APIException():
    status: str
    minQlt: str
    reliability: str
    docuType: str
    ocrResult: str
    ex: Exception

    def __init__(
        self,
        *,
        status: str = "9400",
        minQlt: str = "00",
        reliability: str = "",
        docuType: str = "",
        ocrResult: str = "",
    ) -> None:
        self.status = status
        self.minQlt = minQlt
        self.reliability = reliability
        self.docuType = docuType
        self.docuType = docuType
        self.ocrResult = ocrResult
        super().__init__()


class successful(APIException):
    def __init__(self, reliability, docuType, ocrResult, ex: Exception = None) -> None:
        super().__init__(
            status="1200",
            minQlt=f"00",
            reliability=reliability,
            docuType=docuType,
            ocrResult=ocrResult,
        )


class minQltException(APIException):
    def __init__(self, minQlt, ex: Exception = None) -> None:
        super().__init__(
            status="1400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )


class serverException(APIException):
    def __init__(self, minQlt, ex: Exception = None) -> None:
        super().__init__(
            status="2400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )


class inferenceResultException(APIException):
    def __init__(self, minQlt, ex: Exception = None) -> None:
        super().__init__(
            status="3400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )


class serverTemplateException(APIException):
    def __init__(self, minQlt, ex: Exception = None) -> None:
        super().__init__(
            status="4400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )


class inferenceReliabilityException(APIException):
    def __init__(self, minQlt, reliability, ex: Exception = None) -> None:
        super().__init__(
            status="5400",
            minQlt=minQlt,
            reliability=reliability,
            docuType="",
            ocrResult="",
        )


class ocrResultEmptyException(APIException):
    def __init__(self, minQlt, reliability, ex: Exception = None) -> None:
        super().__init__(
            status="6400",
            minQlt=minQlt,
            reliability=reliability,
            docuType="",
            ocrResult="",
        )


class timeoutException(APIException):
    def __init__(self, minQlt, description, ex: Exception = None) -> None:
        super().__init__(
            status="7400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )
        self.description = description


class parameterException(APIException):
    def __init__(self, minQlt, description, ex: Exception = None) -> None:
        super().__init__(
            status="8400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )
        self.description = description


class otherException(APIException):
    def __init__(self, minQlt, description, ex: Exception = None) -> None:
        super().__init__(
            status="9400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
        )
        self.description = description
