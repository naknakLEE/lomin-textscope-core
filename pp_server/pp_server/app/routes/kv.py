import sys
import traceback

from loguru import logger
from fastapi import Body
from typing import Any
from fastapi import APIRouter

from pp_server.app.common.const import get_settings
from pp_server.app.postprocess.idcard import parse_results


settings = get_settings()
router = APIRouter()


@router.post("/kv")
async def kv(data: dict = Body(...)) -> Any:
    try:
        result = parse_results(
            kv_boxes=data["boxes"],
            kv_scores=data["scores"],
            kv_classes=data["classes"],
            texts=data["texts"],
            id_type=data["id_type"],
        )
        logger.info(f"texts: {result}")
    except:
        logger.exception("idcard post processing")
        result = None
    return {"result": result}
