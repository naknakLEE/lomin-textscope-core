import base64

from httpx import Client
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


from app.database import query
from app.utils.logging import logger
from app.wrapper.pipeline import rotator
from app.schemas import error_models as ErrorResponse
from app.utils.image import rotate_image, bytes_2_pil_image, pil_image_to_base64




def request_rotator(
        session: Session, 
        document_id: str, 
        document_bytes: bytes
    ):
    query_res = query.select_inference_allow_none(session, document_id = document_id)
    if query_res and query_res.inference_result.get("angle"):
        angle = query_res.inference_result.get("angle")
    else:
        
        
        rotator_inputs = {
            "image_bytes": base64.b64encode(document_bytes).decode("utf-8"),
            "image_path": "test.jpg",
            "rectify": {
                "rotation_90n": True,
                "rotation_fine": True
            }
        }
        
        with Client() as client:
            status_code, res, response_log = rotator(client, rotator_inputs)

        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            status_code, error = ErrorResponse.ErrorCode.get(3501)
            logger.error(f"CORE - inference server error")
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        angle = res.get("angle")
    pil_image = bytes_2_pil_image(document_bytes)
    pil_image = rotate_image(pil_image, angle)
    document_base64 = pil_image_to_base64(pil_image, "JPEG")
    return document_base64