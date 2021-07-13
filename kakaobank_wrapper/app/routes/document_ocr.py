import httpx

from typing import Any, Optional, List, Dict
from fastapi import Request, APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from loguru import logger

from kakaobank_wrapper.app import models
from kakaobank_wrapper.app.errors import exceptions as ex
from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.utils.request_form_parser import parse_multi_form
from kakaobank_wrapper.app.utils.ocr_result_parser import parse_kakaobank
from kakaobank_wrapper.app.utils.ocr_response_parser import response_handler


router = APIRouter()
settings = get_settings()
textscope_server_url = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


async def check_document_required_params(lnbzDocClcd: str, pwdNo: str) -> None:
    if lnbzDocClcd not in settings.DOCUMENT_TYPE_LIST:
        result = await response_handler(
            status=8400, minQlt="00", description=f"{lnbzDocClcd} is not valid lnbzDocClcd value"
        )
        raise HTTPException(status_code=200, detail=result)

    if lnbzDocClcd == "D53" and pwdNo == None:
        result = await response_handler(
            status=8400, minQlt="00", description="D53 required parameter not included"
        )
        raise HTTPException(status_code=200, detail=result)


async def get_ocr_request_data(request: Request) -> List[Dict]:
    form_data = await request.form()
    form_data = await parse_multi_form(form_data)

    if "edmisId" not in form_data or "imgFiles" not in form_data:
        result = await response_handler(
            status=4400, description="edmisId or imgFiles is not found", minQlt="00"
        )
        raise HTTPException(status_code=200, detail=result)

    edmisIds = form_data["edmisId"]
    img_files = form_data["imgFiles"]
    if len(edmisIds) != len(img_files):
        result = await response_handler(
            status=4400, description="Different number of edmisId and imgFiles", minQlt="00"
        )
        raise HTTPException(status_code=200, detail=result)
    return [edmisIds, img_files]


async def parse_response(result: Dict, lnbzDocClcd: str) -> Dict:
    if "code" not in result:  # Invalid return if code is not include in response
        raise HTTPException(status_code=200, detail=vars(ex.serverException(minQlt="00")))
    result["status"] = int(result["code"])
    del result["code"]
    if result["status"] >= 1400:
        result = await response_handler(**result)
    else:
        result["ocrResult"] = await parse_kakaobank(
            result["ocrResult"], settings.DOCUMENT_TYPE_SET[lnbzDocClcd]
        )
        result = await response_handler(**result)
    return result


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

    await check_document_required_params(lnbzDocClcd, pwdNo)
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
            files = {"image": file_bytes}
            response = await client.post(
                f"{textscope_server_url}/v12/inference/pipeline",
                files=files,
                params=data,
                timeout=30.0,
            )
            result = response.json()
            parse_result = await parse_response(result, lnbzDocClcd)
            if parse_result.get("status") >= 2000:
                raise HTTPException(status_code=200, detail=parse_result)
            results.append(parse_result)
    return JSONResponse(status_code=200, content=jsonable_encoder(results))
