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


@app.post("/ocr")
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
            files = {"file_bytes": ("documment_img.jpg", file_bytes)}
            response = await client.post(
                f"{TEXTSCOPE_SERVER_URL}/v1/inference/pipeline", files=files, timeout=30.0
            )
            result = response.json()
            results.append(models.InferenceResponse(ocrResult=result))

    return results


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
