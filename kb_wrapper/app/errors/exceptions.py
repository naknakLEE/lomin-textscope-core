async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error


class APIException:
    status: str
    docuType: str
    ocrResult: str
    ex: Exception

    def __init__(
        self,
        *,
        status: str = "9400",
        docuType: str = "",
        ocrResult: str = "",
    ) -> None:
        self.status = status
        self.docuType = docuType
        self.docuType = docuType
        self.ocrResult = ocrResult
        super().__init__()


class serverException(APIException):
    def __init__(self, ex: Exception = None) -> None:
        super().__init__(
            status="2400",
            docuType="",
            ocrResult="",
        )


class inferenceResultException(APIException):
    def __init__(self, ex: Exception = None) -> None:
        super().__init__(
            status="3400",
            docuType="",
            ocrResult="",
        )


class serverTemplateException(APIException):
    def __init__(self, ex: Exception = None) -> None:
        super().__init__(
            status="4400",
            docuType="",
            ocrResult="",
        )


class timeoutException(APIException):
    def __init__(self, description, ex: Exception = None) -> None:
        super().__init__(
            status="7400",
            docuType="",
            ocrResult="",
        )
        self.description = description


class parameterException(APIException):
    def __init__(self, description, ex: Exception = None) -> None:
        super().__init__(
            status="8400",
            description=description,
            docuType="",
            ocrResult="",
        )
        self.description = description


class otherException(APIException):
    def __init__(self, description, ex: Exception = None) -> None:
        super().__init__(
            status="9400",
            docuType="",
            ocrResult="",
        )
        self.description = description


# class requestParameterPairException(APIException):
#     def __init__(self, , description, ex: Exception = None) -> None:
#         super().__init__(
#             status="9400",
#             =,
#             reliability="",
#             docuType="",
#             ocrResult="",
#         )
#         self.description = description
