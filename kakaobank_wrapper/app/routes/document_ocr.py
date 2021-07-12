import http
import httpx

from typing import Any, Optional
from fastapi import Request, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from loguru import logger

from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.errors import exceptions as ex
from kakaobank_wrapper.app.errors.exceptions import HTTPException
from kakaobank_wrapper.app import models
from kakaobank_wrapper.app.utils.ocr_result_parser import parse_kakaobank
from kakaobank_wrapper.app.utils.ocr_response_parser import response_handler
from kakaobank_wrapper.app.utils.request_parser import parse_multi_form


router = APIRouter()
settings = get_settings()
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


async def check_D53_document_required_params(lnbzDocClcd: str, pwdNo: str):
    if lnbzDocClcd == "D53" and pwdNo == None:
        result = response_handler(
            status=8400, minQlt="00", description="D53 required parameter not included"
        )
        return HTTPException(status_code=200, detail=result)


async def get_ocr_request_data(request: Request):
    form_data = await request.form()
    form_data = parse_multi_form(form_data)

    if "edmisId" not in form_data or "imgFiles" not in form_data:
        result = response_handler(
            status=4400, description="edmisId or imgFiles is not found", minQlt="00"
        )
        raise HTTPException(status_code=200, detail=result)

    edmisIds = form_data["edmisId"]
    img_files = form_data["imgFiles"]
    if len(edmisIds) != len(img_files):
        result = response_handler(
            status=4400, description="Different number of edmisId and imgFiles", minQlt="00"
        )
        return HTTPException(status_code=200, detail=result)

    return edmisIds, img_files


@router.post("/ocr", status_code=200)
async def inference(
    request: Request,
    lnbzDocClcd: str,
    lnbzMgntNo: str,
    pwdNo: Optional[str] = None,
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """

    await check_D53_document_required_params(lnbzDocClcd, pwdNo)
    edmisIds, img_files = await get_ocr_request_data(request)

    data = {
        "lnbzDocClcd": lnbzDocClcd,
        "lnbzMgntNo": lnbzMgntNo,
        "pwdNo": pwdNo,
    }
    results = list()
    async with httpx.AsyncClient() as client:
        for file, edmisId in zip(img_files.values(), edmisIds):
            data["edmisId"] = edmisId
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
                    result["ocrResult"], settings.DOCUMENT_TYPE_SET[lnbzDocClcd]
                )
                result = response_handler(**result)
                results.append(models.InferenceResponse(**result))
    return JSONResponse(status_code=200, content=jsonable_encoder(results))
