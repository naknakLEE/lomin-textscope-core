import uvicorn
import os
import asyncio
import httpx

from typing import Any, List
from fastapi import FastAPI, Request, Depends
from fastapi import Depends, File, UploadFile, APIRouter

# from fastapi.security import OAuth2PasswordBearer
# from dataclasses import asdict
# from prometheusrock import PrometheusMiddleware, metrics_route

from app.common.const import get_settings
from app import models
from kakaobank_wrapper.app.errors import exceptions as ex

# from app.database.connection import db
# from app.common.config import config
# from app.database.schema import create_db_table
# from app.middlewares.logging import LoggingMiddleware
# from app.middlewares.timeout_handling import TimeoutMiddleware
# from app.errors import exceptions as ex


settings = get_settings()
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


def create_app() -> FastAPI:
    app = FastAPI()

    return app


os.environ["API_ENV"] = "production"
app = create_app()


@app.post("/ocr", status_code=200)
async def inference(files: List[UploadFile] = File(...)) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    # file = await file.read()
    # return len(files)

    results = []
    async with httpx.AsyncClient() as client:
        for file in files:
            file_bytes = await file.read()
            files = {"image": ("documment_img.jpg", file_bytes)}
            response = await client.post(
                f"{TEXTSCOPE_SERVER_URL}/v1/inference/pipeline", files=files, timeout=30.0
            )
            result = response.json()

            print("\033[95m" + f"{result}" + "\033[m")
            minQlt, description, reliability, docuType, ocrResult = "", "", "", "", {}
            if result["status"] == 400: # bad request
                ...
            elif result["status"] == 403: # forbidden
                ...
            elif result["status"] == 404: # not found
                ...
            elif result["status"] == 502: # bad gateway
                ...
            elif result["status"] == 503: # service unavailable
                ...
            elif result["status"] == 1200:
                result = ex.minQltException(minQlt, reliability, docuType, ocrResult)
            elif result["status"] == 1400:
                result = ex.minQltException(minQlt)
                "최소퀄리티 미달"
            elif result["status"] == 2400:
                result = ex.serverException(minQlt)
                "엔진 서버 미응답"
            elif result["status"] == 3400:
                result = ex.inferenceResultException(minQlt)
                "OCR 엔진 인식결과 이상"
            elif result["status"] == 4400:
                result = ex.serverTemplateException(minQlt)
                "문서종류가 상이"
            elif result["status"] == 5400:
                result = ex.inferenceReliabilityException(minQlt, reliability)
                "인식결과 신뢰도 낮음"
            elif result["status"] == 6400:
                result = ex.ocrResultEmptyException(minQlt, reliability)
                "등기필증 인식 실패"
            elif result["status"] == 7400:
                result = ex.timeoutException(minQlt, description)
                "Timeout 발생"
            elif result["status"] == 8400:
                result = ex.parameterException(minQlt, description)
                "Error Response"
            elif result["status"] == 9400:
                result = ex.otherException(minQlt, description)
                "Error Response"

            elif result["status"] >= 405 or result["status"] < 200:
                result = ex.otherException().__dict__

            
            results.append(models.InferenceResponse(**result))

    return results


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
