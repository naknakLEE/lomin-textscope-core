from typing import Optional


class ErrorCode:
    RESOURCE_DATA = "4000"


class StatusCode:
    HTTP_500 = 500
    HTTP_400 = 400
    HTTP_401 = 401
    HTTP_403 = 403
    HTTP_404 = 404
    HTTP_405 = 405
    HTTP_416 = 416


class APIException(Exception):
    status_code: int
    code: str
    msg: Optional[str]
    detail: Optional[str]
    exc: Optional[Exception]

    def __init__(
        self,
        *,
        status_code: int = StatusCode.HTTP_500,
        code: str = "500",
        msg: str = None,
        detail: str = None,
        exc: Optional[Exception] = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.exc = exc
        super().__init__(exc)


class InferenceException(APIException):
    def __init__(
        self,
        message: str = None,
        detail: str = None,
        exc: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_416,
            code="8400",
            msg=f"{message}",
            detail=f"{detail}",
            exc=exc,
        )


class NotFoundUserException(APIException):
    def __init__(self, email: str, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_404,
            msg=f"Incorrect email or password",
            detail=f"Not Found User: {email}",
            code="8400",
            exc=exc,
        )


class PrivielgeException(APIException):
    def __init__(self, email: str, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user doesn't have enough privileges",
            detail=f"{email} doesn't have enough privileges",
            code="8400",
            exc=exc,
        )


class AlreadyExistUserException(APIException):
    def __init__(self, email: str = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user with this email already exists in the system.",
            detail=f"{email} already exists in the system",
            code="8400",
            exc=exc,
        )


class JWTNotFoundUserException(APIException):
    def __init__(self, email: str, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valemailate credentials",
            detail=f"Not Found User email: {email}",
            code="8400",
            exc=exc,
        )


class JWTExpiredExetpion(APIException):
    def __init__(self, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"Session has expired and logged out",
            detail="",
            code="8400",
            exc=exc,
        )


class JWTException(APIException):
    def __init__(self, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valilate credentials",
            detail="",
            code="8400",
            exc=exc,
        )


class JWTScopeException(APIException):
    def __init__(
        self, authenticate_value: str, exc: Optional[Exception] = None
    ) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Not enough permissions",
            detail=authenticate_value,
            code="8400",
            exc=exc,
        )


class NotAuthenticatedException(APIException):
    def __init__(self, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_403,
            msg=f"Not authenticated",
            detail="Not authenticated",
            code="8400",
            exc=exc,
        )


class TimeoutException(APIException):
    def __init__(self, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_403,
            msg=f"timeout exception",
            detail="",
            code="7400",
            exc=exc,
        )


class InferenceServerException(APIException):
    def __init__(self, exc: Optional[Exception] = None) -> None:
        super().__init__(
            status_code=2400,
            msg=f"timeout exception",
            detail="",
            code="8400",
            exc=exc,
        )


class ResourceDataError(Exception):
    code: str
    message: Optional[str]
    detail: Optional[str]
    exc: Optional[Exception]

    def __init__(
        self,
        code: str = ErrorCode.RESOURCE_DATA,
        message: str = None,
        detail: str = None,
        exc: Optional[Exception] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        self.exc = exc
        super().__init__(exc)


# TODO: status code ???????????? ??????
class ExtractException(APIException):
    def __init__(self, msg: str, exc: Exception = None) -> None:
        super().__init__(
            status_code=415,
            msg=msg,
            detail="",
            code="8500",
            exc=exc,
        )


class NotExistException(APIException):
    def __init__(self, msg: str, exc: Exception = None) -> None:
        super().__init__(
            status_code=415,
            msg=msg,
            detail="",
            code="8600",
            exc=exc,
        )
    

class ValidationFailedException(APIException):
    def __init__(self, msg: str, exc: Exception = None) -> None:
        super().__init__(
            status_code=415,
            msg=msg,
            detail="",
            code="8700",
            exc=exc,
        )

class AlreadyExistDataException(APIException):
    def __init__(self, target: str = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"This {target} already exist",
            detail="",
            code="8800",
            exc=exc,
        )