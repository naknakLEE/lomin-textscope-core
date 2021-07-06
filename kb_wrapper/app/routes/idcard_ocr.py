import httpx

from typing import Any
from fastapi import Request, APIRouter, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from kb_wrapper.app import models
from kb_wrapper.app.errors import exceptions as ex
from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.utils.request_parser import parse_multi_form
from kb_wrapper.app.utils.ocr_result_parser import parse_kakaobank
from kb_wrapper.app.utils.ocr_response_parser import response_handler


router = APIRouter()
settings = get_settings()
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


@router.post("/kb", status_code=200)
async def inference(
    image_path: str = Form(...),
    request_id: str = Form(...),
    doc_type: str = Form(...),
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": doc_type,
    }
    results = list()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TEXTSCOPE_SERVER_URL}/v1/inference/kb/idcard",
            data=data,
            timeout=300.0,
        )
        result = response.json()
        print("\033[95m" + f"{result}" + "\033[m")
        result["status"] = int(result["code"])
        del result["code"]
        if result["status"] >= 1400:
            result = response_handler(**result)
            results.append(models.SuccessfulResponse(**result))
        else:
            result["ocrResult"] = parse_kakaobank(result["ocrResult"])
            result = response_handler(**result)
            results.append(models.SuccessfulResponse(**result))
    return JSONResponse(status_code=200, content=jsonable_encoder(results))
