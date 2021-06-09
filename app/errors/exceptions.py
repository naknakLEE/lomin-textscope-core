async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
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
    ex: Exception

    def __init__(
        self,
        *,
        status_code: int = StatusCode.HTTP_500,
        code: str = "000000",
        msg: str = None,
        detail: str = None,
        ex: Exception = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.ex = ex
        super().__init__(ex)


class InferenceException(APIException):
    def __init__(
        self, 
        code: str = None, 
        message: str = None, 
        ex: Exception = None
        ) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_416,
            code=f"{code}",
            msg=f"{message}",
            detail=None,
            ex=ex,
        )


class NotFoundUserException(APIException):
    def __init__(self, email: int = None, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_404,
            msg=f"Incorrect email or password",
            detail=f"Not Found User email: {email}",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class PrivielgeException(APIException):
    def __init__(self, email: int = None, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user doesn't have enough privileges",
            detail=f"{email} doesn't have enough privileges",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class AlreadyExistException(APIException):
    def __init__(self, email: int = None, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"The user with this email already exists in the system.",
            detail=f"{email} already exists in the system",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class JWTNotFoundUserException(APIException):
    def __init__(self, email: str = None, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valemailate credentials",
            detail=f"Not Found User email: {email}",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class JWTExpiredExetpion(APIException):
    def __init__(self, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"Session has expired and logged out",
            detail="Token Expired",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class JWTException(APIException):
    def __init__(self, JWTError: str = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not valemailate credentials",
            detail="JWTError",
            code=f"{'1'.zfill(4)}",
            ex=JWTError,
        )


class NotAuthenticatedException(APIException):
    def __init__(self, ex: Exception = None) -> None:
        super().__init__(
            status_code=StatusCode.HTTP_403,
            msg=f"Not authenticated",
            detail="Not authenticated",
            code=f"{'1'.zfill(4)}",
            ex=ex,
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
