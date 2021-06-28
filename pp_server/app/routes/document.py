import time
import asyncio
import numpy as np

from fastapi import Body
from typing import Any
from fastapi import APIRouter

from app.serving.utils.catalogs import ELabelCatalog
from app.serving.utils.envs import logger
from app.common.const import get_settings
from lovit.utils.converter import CharacterMaskGenerator, build_converter


settings = get_settings()
router = APIRouter()
characters = ELabelCatalog.get(
    ("num", "eng_cap", "eng_low", "kor_2350", "symbols"), decipher=settings.DECIPHER
)

converter = build_converter(characters, True)


def convert_recognition_to_text(rec_preds):
    texts = converter.decode(rec_preds, [rec_preds.shape[0]] * len(rec_preds))
    texts = [_t[: _t.find("[s]")] for _t in texts]
    return texts


@router.post("/document_ocr")
async def inference(data: dict = Body(...)) -> Any:
    asyncio.sleep(10)
    rec_preds = np.array(data["rec_preds"])
    start_t = data["start_t"]
    texts = convert_recognition_to_text(rec_preds)
    logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    return {"texts": texts}
