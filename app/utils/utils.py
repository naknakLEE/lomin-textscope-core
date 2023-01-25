from typing import Dict, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.common.const import get_settings


settings = get_settings()
pp_mapping_table = settings.PP_MAPPING_TABLE


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
    elif doc_type.split("_")[0] in pp_mapping_table.get("seal_imp_cert"):
        return "seal_imp_cert"
    elif doc_type.split("_")[0] in pp_mapping_table.get("ccr"):
        return "ccr"
    return None