from pp_server.app.postprocess.commons import BoxlistPostprocessor
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

# from pp_server.app.postprocess import basic_cert, family_cert, regi_cert, rrtable
from pp_server.app.postprocess import family_cert, basic_cert, rrtable, regi_cert
from pp_server.app.structures.bounding_box import BoxList


postprocess_basic_cert = basic_cert.postprocess_basic_cert
postprocess_family_cert = family_cert.postprocess_family_cert
postprocess_regi_cert = regi_cert.postprocess_regi_cert
postprocess_rrtable = rrtable.postprocess_rrtable


settings = get_settings()
router = APIRouter()
characters = ELabelCatalog.get(
    ("digits", "eng_cap", "eng_low", "basic_symbol", "kor_2350", "kor_jamo"),
    decipher=settings.DECIPHER,
)

converter = build_converter(characters, True)


def convert_recognition_to_text(rec_preds):
    texts = converter.decode(rec_preds, [rec_preds.shape[0]] * len(rec_preds))
    # texts = [_t[: _t.find("[s]")] for _t in texts]
    texts = [_t.replace("[others]", "") for _t in texts]
    texts = [_t[: _t.find("[s]")] if "[s]" in _t else _t for _t in texts]
    texts = ["" if _t is None else _t for _t in texts]
    return texts


@router.post("/idcard")
async def idcard(data: dict = Body(...)) -> Any:
    asyncio.sleep(10)
    rec_preds = np.array(data["rec_preds"])[0][0]
    start_t = data["start_t"]
    print(f"rec_preds: {rec_preds.shape}")
    result = convert_recognition_to_text(rec_preds)
    logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    return {"texts": result}


def create_boxlist(data):
    for attr in data:
        if attr == "rec_preds":
            print("\033[96m" + f"{np.array(data[attr]).shape}" + "\033[m")
        else:
            print("\033[96m" + f"{np.array(data[attr]).shape}" + "\033[m")
    texts = convert_recognition_to_text(np.array(data["rec_preds"]))
    print("\033[95m" + f"texts: {texts}" + "\033[m")
    boxlist = BoxList(np.array(data["boxes"]), np.array(data["img_size"]))
    boxlist.add_field("scores", np.array(data["scores"]))
    boxlist.add_field("texts", texts)
    return boxlist


@router.post("/postprocess_basic_cert")
async def basic_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_basic_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result}, debug_dic: {debug_dic}" + "\033[m")
    return {"texts": result, "debug_dic": debug_dic}


@router.post("/postprocess_family_cert")
async def family_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_family_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    # print("\033[95m" + f"texts: {result}, debug_dic: {debug_dic}" + "\033[m")
    return {"texts": result}


@router.post("/postprocess_rrtable")
async def rrtable(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_rrtable(boxlist, 0.5, [])
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result.values}, debug_dic: {debug_dic.values}" + "\033[m")

    return {"texts": result, "debug_dic": debug_dic}


@router.post("/postprocess_regi_cert")
async def regi_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_regi_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result.values}, debug_dic: {debug_dic.values}" + "\033[m")
    return {"texts": result, "debug_dic": debug_dic}
