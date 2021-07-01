from fastapi.encoders import jsonable_encoder
import uvicorn
import os
import asyncio
import httpx

from starlette.middleware.base import RequestResponseEndpoint, BaseHTTPMiddleware
from typing import Any, List
from dataclasses import asdict
from fastapi import FastAPI, Request, Depends, Response
from fastapi import Depends, File, UploadFile, APIRouter
from fastapi.responses import JSONResponse

# from fastapi.security import OAuth2PasswordBearer
# from dataclasses import asdict
# from prometheusrock import PrometheusMiddleware, metrics_route

from app.common.const import get_settings
from app.common.config import config
from kakaobank_wrapper.app.database.schema import create_db_table
from kakaobank_wrapper.app.database.connection import db
from app import models
from kakaobank_wrapper.app.errors import exceptions as ex
from kakaobank_wrapper.app.utils.parse import parse_kakaobank

# from app.database.connection import db
# from app.common.config import config
# from app.database.schema import create_db_table
# from app.middlewares.logging import LoggingMiddleware
# from app.middlewares.timeout_handling import TimeoutMiddleware
# from app.errors import exceptions as ex


settings = get_settings()
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"
DOCUMENT_TYPE_SET = {
    "D01": "rrtable",
    "D02": "family_cert",
    "D03": "basic_cert",
    "D04": "regi_cert",
}


def create_app() -> FastAPI:
    app = FastAPI()

    # db.init_app(app, **asdict(config()))
    # create_db_table()

    return app


os.environ["API_ENV"] = "production"
app = create_app()


def response_handler(
    status: int,
    minQlt: str = "",
    description: str = "",
    reliability: str = "",
    docuType: str = "",
    ocrResult: dict = {},
    msg: str = "",
    detail: str = "",
    status_code: str = "",
    exc: Exception = None,
):
    if status == 1200:
        result = ex.minQltException(
            minQlt=minQlt,
            reliability=reliability,
            docuType=docuType,
            ocrResult=ocrResult,
        )
    elif status == 1400:
        result = ex.minQltException(minQlt=minQlt)
        "최소퀄리티 미달"
    elif status == 2400 or status == 500:
        result = ex.serverException(minQlt=minQlt)
        "엔진 서버 미응답"
    elif status == 3400:
        result = ex.inferenceResultException(minQlt=minQlt)
        "OCR 엔진 인식결과 이상"
    elif status == 4400:
        result = ex.serverTemplateException(minQlt=minQlt)
        "문서종류가 상이"
    elif status == 5400:
        result = ex.inferenceReliabilityException(minQlt=minQlt, reliability=reliability)
        "인식결과 신뢰도 낮음"
    elif status == 6400:
        result = ex.ocrResultEmptyException(minQlt=minQlt, reliability=reliability)
        "등기필증 인식 실패"
    elif status == 7400:
        result = ex.timeoutException(minQlt=minQlt, description=description)
        "Timeout 발생"
    elif status == 8400:
        result = ex.parameterException(minQlt=minQlt, description=msg)
        "Error Response"
    elif status == 9400:
        result = ex.otherException(minQlt=minQlt, description=description)
        "Error Response"
    elif status >= 405 or status < 200:
        result = ex.otherException(minQlt=minQlt, description=description)
    elif status == 400:
        result = ex.otherException(minQlt=minQlt, description=description)
        "bad request"
    elif status == 403:
        result = ex.otherException(minQlt=minQlt, description=description)
        "forbidden"
    elif status == 404:
        result = ex.otherException(minQlt=minQlt, description=description)
        "not found"
    elif status == 502:
        result = ex.otherException(minQlt=minQlt, description=description)
        "bad gateway"
    elif status == 503:
        result = ex.otherException(minQlt=minQlt, description=description)
        "service unavailable"
    return result.__dict__


class catch_exceptions_middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            response = response_handler(status=2400)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPStatusError as exc:
            print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            response = response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
        # except Exception as error:
        #     print('\033[95m' + f"{error}" + '\033[95m')
        #     response = response_handler(status=9400)
        #     return JSONResponse(status_code=200, content=response)


app.add_middleware(catch_exceptions_middleware)


@app.post("/ocr", status_code=200)
async def inference(
    edmisid: str,
    InbzDocClcd: str,
    InbzMgntNo: str,
    PwdCnt: str,
    files: List[UploadFile] = File(...),
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    data = {
        "edmisid": edmisid,
        "InbzDocClcd": InbzDocClcd,
        "InbzMgntNo": InbzMgntNo,
        "PwdCnt": PwdCnt,
    }
    results = list()
    async with httpx.AsyncClient() as client:
        for file in files:
            file_bytes = await file.read()
            files = {"image": ("documment_img.jpg", file_bytes)}
            response = await client.post(
                f"{TEXTSCOPE_SERVER_URL}/v1/inference/pipeline",
                files=files,
                params=data,
                timeout=30.0,
            )
            result = response.json()
            print("\033[95m" + f"{result}" + "\033[m")
            result["status"] = int(result["code"])
            del result["code"]
            if result["status"] >= 1400:
                result = response_handler(**result)
                results.append(models.InferenceResponse(**result))
            else:
                result["ocrResult"] = parse_kakaobank(
                    result["ocrResult"], DOCUMENT_TYPE_SET[InbzDocClcd]
                )
                result = response_handler(**result)
                results.append(models.InferenceResponse(**result))
    return JSONResponse(status_code=200, content=jsonable_encoder(results))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
