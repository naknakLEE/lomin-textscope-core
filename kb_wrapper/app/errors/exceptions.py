async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error


class APIException:
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
            description=description,
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


# class requestParameterPairException(APIException):
#     def __init__(self, minQlt, description, ex: Exception = None) -> None:
#         super().__init__(
#             status="9400",
#             minQlt=minQlt,
#             reliability="",
#             docuType="",
#             ocrResult="",
#         )
#         self.description = description
