from typing import Dict, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def set_error_response(code: str, ocr_result: Dict = {}, message: str = "") -> JSONResponse:
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
    if doc_type.split("_")[0] in ["Z1", "Z2", "Z3"]:
        return "kv"
    elif "인감증명서" in doc_type:
        return "seal_imp_cert"
    elif "법인등기부" in doc_type:
        return "ccr"
    return None