async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(exc=error, detail=str(error))
    return error


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
    msg: str
    detail: str
    exc: Exception

    def __init__(
        self,
        *,
        status_code: int = StatusCode.HTTP_500,
        code: str = "8400",
        msg: str = None,
        detail: str = None,
        exc: Exception = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.exc = exc
        super().__init__(exc)


class InferenceException(APIException):
    def __init__(
        self, code: str = None, message: str = None, exc: Exception = None
    ) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_416,
            code=f"{code}",
            msg=f"{message}",
            detail=None,
            exc=exc,
        )


class NotFoundUserException(APIException):
    def __init__(self, email: int = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_404,
            msg=f"Incorrect email or password",
            detail=f"Not Found User email: {email}",
            code=8400,
            exc=exc,
        )


class PrivielgeException(APIException):
    def __init__(self, email: int = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user doesn't have enough privileges",
            detail=f"{email} doesn't have enough privileges",
            code=8400,
            exc=exc,
        )


class AlreadyExistException(APIException):
    def __init__(self, email: int = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user with this email already exists in the system.",
            detail=f"{email} already exists in the system",
            code=8400,
            exc=exc,
        )


class JWTNotFoundUserException(APIException):
    def __init__(self, email: str = None, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valemailate credentials",
            detail=f"Not Found User email: {email}",
            code=8400,
            exc=exc,
        )


class JWTExpiredExetpion(APIException):
    def __init__(self, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"Session has expired and logged out",
            detail="",
            code=8400,
            exc=exc,
        )


class JWTException(APIException):
    def __init__(self, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valilate credentials",
            detail="",
            code=8400,
            exc=exc,
        )


class JWTScopeException(APIException):
    def __init__(self, exc: Exception = None, authenticate_value: str = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Not enough permissions",
            detail=authenticate_value,
            code=8400,
            exc=exc,
        )


class NotAuthenticatedException(APIException):
    def __init__(self, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_403,
            msg=f"Not authenticated",
            detail="Not authenticated",
            code=8400,
            exc=exc,
        )


class TimeoutException(APIException):
    def __init__(self, exc: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_403,
            msg=f"timeout exception",
            detail="",
            code="7400",
            exc=exc,
        )


class InferenceServerException(APIException):
    def __init__(self, exc: Exception = None) -> None:
        super().__init__(
            status_code=2400,
            msg=f"timeout exception",
            detail="",
            code=8400,
            exc=exc,
        )


# class UnicornException(Exception):
#     def __init__(self, name: str):
#         self.name = name


# @app.exception_handler(UnicornException)
# async def uvicorn_exception_handler(request: Request, exc: UnicornException):
#     return JSONResponse(
#         status_code=418,
#         content={"message": f"Oops! {exc.name} demail something. There goes a rainbows..."},
#     )


# class InferenceException(Exception):
#     def __init__(self, error, status_code) -> None:
#         self.error = error
#         self.status_code = status_code
