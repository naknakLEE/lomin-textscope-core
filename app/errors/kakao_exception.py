async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error



class APIException(Exception):
    status_code: str
    minQlt: str
    reliability: str
    docuType: str
    ocrResult: str
    ex: Exception

    def __init__(
        self,
        *,
        status_code: str = "0000",
        minQlt: str = "000000",
        reliability: str = None,
        docuType: str = None,
        ocrResult: str = None,
        ex
    ) -> None:
        self.status_code = status_code
        self.minQlt = minQlt
        self.reliability = reliability
        self.docuType = docuType
        self.docuType = docuType
        self.ocrResult = ocrResult
        self.ex = ex
        super().__init__(ex)


class successful(APIException):
    def __init__(
        self, 
        reliability,
        docuType,
        ocrResult,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="1200",
            minQlt=f"00",
            reliability=reliability,
            docuType=docuType,
            ocrResult=ocrResult,
            ex=ex,
        )

class minQltException(APIException):
    def __init__(
        self, 
        minQlt,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="1400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
            ex=ex,
        )


class serverException(APIException):
    def __init__(
        self, 
        minQlt,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="2400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
            ex=ex,
        )


class inferenceResultException(APIException):
    def __init__(
        self, 
        minQlt,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="3400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
            ex=ex,
        )

        
class serverTemplateException(APIException):
    def __init__(
        self, 
        minQlt,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="4400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
            ex=ex,
        )


class inferenceReliabilityException(APIException):
    def __init__(
        self, 
        minQlt,
        reliability,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="5400",
            minQlt=minQlt,
            reliability=reliability,
            docuType="",
            ocrResult="",
            ex=ex,
        )


class otherException(APIException):
    def __init__(
        self, 
        minQlt,
        reliability,
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code="6400",
            minQlt=minQlt,
            reliability="",
            docuType="",
            ocrResult="",
            ex=ex,
        )
