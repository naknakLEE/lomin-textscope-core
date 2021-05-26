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
    ):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.ex = ex
        super().__init__(ex)


class InferenceException(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=500,
            code="T5001",
            msg=f"Unable to extract information from id card",
            detail="",
            ex=ex,
        )


class InferenceException(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


class NotFoundUserEx(APIException):
    def __init__(self, user_id: int = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_404,
            msg=f"Incorrect username or password",
            detail=f"Not Found User ID : {user_id}",
            code=f"{StatusCode.HTTP_400}",
            ex=ex,
        )


class InferenceException(APIException):
    def __init__(self, code: str = None, message: str = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"{message}",
            detail=None,
            code=f"{code}",
            ex=ex,
        )


class NotFoundUserException(APIException):
    def __init__(self, username: str = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not validate credentials",
            detail=f"Not Found User: {username}",
            code=f"{'1'.zfill(4)}",
            ex=ex,
        )


class JWTException(APIException):
    def __init__(self, JWTError: str = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_401,
            msg=f"Could not validate credentials",
            detail="JWTError",
            code=f"{'1'.zfill(4)}",
            ex=JWTError,
        )


class JWTExpiredExetpion(APIException):
    def __init__(self, username: str = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_400,
            msg=f"Session has expired and logged out",
            detail="Token Expired",
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
#         content={"message": f"Oops! {exc.name} did something. There goes a rainbows..."},
#     )
