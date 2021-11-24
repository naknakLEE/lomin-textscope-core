import base64

from typing import Dict, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from os import environ

from io import BytesIO
from PIL import Image
from app.common.const import get_settings
from datetime import datetime

settings = get_settings()
pp_mapping_table = settings.PP_MAPPING_TABLE
document_type_set = settings.DOCUMENT_TYPE_SET

def set_json_response(code: str, ocr_result: Dict = {}, message: str = "") -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(
            dict(
                code=code,
                ocr_result=ocr_result,
                message=message,
            )
        )
    )


def get_pp_api_name(doc_type: str) -> Union[None, str]:
    if doc_type.split("_")[0] in pp_mapping_table.get("general_pp", []):
        return "kv"
    elif doc_type.split("_")[0] in pp_mapping_table.get("bankbook", []):
        return "bankbook"
    elif doc_type in pp_mapping_table.get("seal_imp_cert", []):
        return "seal_imp_cert"
    elif doc_type in pp_mapping_table.get("ccr", []):
        return "ccr"
    elif settings.CUSTOMER == "kakaobank" and doc_type in document_type_set:
        return document_type_set.get(doc_type)
    return None

def cal_time_elapsed_seconds(start: datetime, end: datetime) -> str:
    elapsed = end - start
    sec, microsec = elapsed.seconds, round(elapsed.microseconds / 1_000_000, 3)
    return f'{sec + microsec}'

def basic_time_formatter(target_time: str):
    return target_time.replace('.', '-', 2).replace('.', '', 1)[:-3]

def load_image2base64(img_path):
    buffered = BytesIO()
    pil_image = Image.open(img_path)
    image_convert_rgb = pil_image.convert("RGB")
    image_convert_rgb.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()) 
    return img_str
