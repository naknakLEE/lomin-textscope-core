from typing import Dict, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from os import environ

from app.common.const import get_settings


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
    if doc_type.split("_")[0] in pp_mapping_table.get("general_pp"):
        return "kv"
    elif doc_type.split("_")[0] in pp_mapping_table.get("bankbook"):
        return "bankbook"
    elif pp_mapping_table.get("seal_imp_cert") in doc_type:
        return "seal_imp_cert"
    elif pp_mapping_table.get("ccr") in doc_type:
        return "ccr"
    elif environ.get("CUSTOMER") == "kakaobank" and doc_type in document_type_set:
        return document_type_set.get(doc_type)
    return None