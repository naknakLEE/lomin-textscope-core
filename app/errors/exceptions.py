from re import L
# from main import app



# class UnicornException(Exception):
#     def __init__(self, name: str):
#         self.name = name


# @app.exception_handler(UnicornException)
# async def uvicorn_exception_handler(request: Request, exc: UnicornException):
#     return JSONResponse(
#         status_code=418,
#         content={"message": f"Oops! {exc.name} did something. There goes a rainbows..."},
#     )


class  StatusCode:
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

    def __init__ (
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



class InferenceError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code