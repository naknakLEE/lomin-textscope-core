import aiohttp
import httpx

from typing import Dict, Any, List, Optional
from fastapi import Depends, File, UploadFile, APIRouter, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
from app.schemas import inference_responses
from app import models


settings = get_settings()
router = APIRouter()

MODEL_SERVER_URL = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
PP_SERVER_URL = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


@router.post(
    "",
    dependencies=[Depends(db.session), Depends(get_current_active_user)],
    response_model=models.InferenceResponse,
    responses=inference_responses,
)
async def inference(file: UploadFile = File(...)) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    serving_server_inference_url = (
        f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference"
    )

    image_data = await file.read()
    async with aiohttp.ClientSession() as session:
        async with session.post(serving_server_inference_url, data=image_data) as response:
            result = await response.json()
            return models.InferenceResponse(ocrResult=result)


@router.post(
    "/tiff/idcard",
    dependencies=[Depends(db.session)],
    responses=inference_responses,
)
async def tiff_idcard_inference(
    image_path: str = Form(...),
    request_id: str = Form(...),
    doc_type: str = Form(...),
    page: str = Form(...),
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    serving_server_inference_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": doc_type,
        "page": page,
    }
    json_data = jsonable_encoder(data)
    # async with aiohttp.ClientSession() as session:
    #     request_api = "tiff_inference"
    #     if json_data["page"] == "None":
    #         request_api = "tiff_inference_all"
    #     async with session.post(
    #         f"{serving_server_inference_url}/{request_api}", json=json_data
    #     ) as response:
    #         result = await response.json()
    #         # return models.InferenceResponse(ocrResult=result)
    #         return result

    if page == "None":
        result = {
            "code": "1000",
            "ocr_result": [
                {"page": "1", "status_code": "100", "doc_type": "신청서"},
                {"page": "2", "status_code": "100", "doc_type": "가맹점가입신청서"},
                {
                    "page": "3",
                    "status_code": "100",
                    "doc_type": "사업자등록증",
                    "kv": {"cbr_business_num": "754-87-00942", "other keys": "other values"},
                },
                {
                    "page": "3",
                    "status_code": "100",
                    "doc_type": "주민등록증",
                    "kv": {
                        "rrc_title": "주민등록증",
                        "rrc_name": "홍길동",
                        "rrc_regnum": "123456-1234567",
                        "rrc_issue_date": "2021.06.30",
                    },
                },
                {
                    "page": "3",
                    "status_code": "100",
                    "doc_type": "운전면허증",
                    "kv": {
                        "dlc_title": "주민등록증",
                        "dlc_name": "홍길동",
                        "dlc_regnum": "123456-1234567",
                        "dlc_issue_date": "2021.06.30",
                        "dlc_license_num": "01-123456-10",
                        "dlc_exp_date": "2022.06.30",
                    },
                },
                {
                    "page": "3",
                    "status_code": "100",
                    "doc_type": "주민등록증",
                    "kv": {
                        "arc_title": "주민등록증",
                        "arc_name": "홍길동",
                        "arc_regnum": "123456-1234567",
                        "arc_issue_date": "2021.06.30",
                    },
                },
            ],
        }
    else:
        result = {
            "code": 1000,
            "image_height": 1756,
            "image_width": 1239,
            "num_instances": 2,
            "page": 1,
            "result": [
                {"bbox": [94, 17, 141, 40], "scores": 0.9995675683021545, "texts": "사람"},
                {"bbox": [154, 17, 195, 40], "scores": 0.9995211362838745, "texts": "중심"},
            ],
        }
    return result


@router.post("/pipeline")
async def inference(
    edmisId: str, lnbzDocClcd: str, lnbzMgntNo: str, PwdNo: str, image: UploadFile = File(...)
) -> Any:
    image_bytes = await image.read()
    files = {"image": ("document_img.jpg", image_bytes)}
    document_type = settings.DOCUMENT_TYPE_SET[lnbzDocClcd]

    async with httpx.AsyncClient() as client:
        document_ocr_model_response = await client.post(
            f"{MODEL_SERVER_URL}/document_ocr", files=files, timeout=300.0
        )
        document_ocr_result = document_ocr_model_response.json()

        document_ocr_pp_response = await client.post(
            f"{PP_SERVER_URL}/post_processing/{document_type}",
            json=document_ocr_result,
            timeout=30.0,
        )
        result = document_ocr_pp_response.json()["texts"]["values"]

    json_compatible_files = jsonable_encoder(
        {
            "code": "1200",
            "description": "",
            "minQlt": "01",
            "reliability": "1.0",
            "docuType": lnbzDocClcd,
            "ocrResult": result,
        }
    )
    return JSONResponse(content=json_compatible_files)
