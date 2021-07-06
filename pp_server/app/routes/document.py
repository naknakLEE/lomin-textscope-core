import httpx
import cv2
from pp_server.app.postprocess.commons import BoxlistPostprocessor
import time
import asyncio
import numpy as np

from fastapi import Body
from typing import Any
from fastapi import APIRouter

from pp_server.app.common.const import get_settings
from pp_server.app.postprocess import family_cert, basic_cert, rrtable, regi_cert
from pp_server.app.structures.bounding_box import BoxList
from pp_server.app.utils import convert_recognition_to_text


postprocess_basic_cert = basic_cert.postprocess_basic_cert
postprocess_family_cert = family_cert.postprocess_family_cert
postprocess_regi_cert = regi_cert.postprocess_regi_cert
postprocess_rrtable = rrtable.postprocess_rrtable


settings = get_settings()
router = APIRouter()


# from app.serving.utils.catalogs import ELabelCatalog, EDocumentCatalog
# from lovit.utils.converter import CharacterMaskGenerator, build_converter
# characters = ELabelCatalog.get(
#     ("num", "eng_cap", "eng_low", "kor_2350", "symbols"), decipher=settings.DECIPHER
# )
# converter = build_converter(characters, True)
# def convert_recognition_to_text(rec_preds):
#     texts = converter.decode(rec_preds, [rec_preds.shape[0]] * len(rec_preds))
#     texts = [_t[: _t.find("[s]")] for _t in texts]
#     return texts


@router.post("/idcard")
async def idcard(data: dict = Body(...)) -> Any:
    asyncio.sleep(10)
    rec_preds = np.array(data["rec_preds"])[0][0]
    start_t = data["start_t"]
    print(f"rec_preds: {rec_preds.shape}")
    result = convert_recognition_to_text(rec_preds)
    print(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    return {"texts": result}


def create_boxlist(data):
    for attr in data:
        if attr == "rec_preds":
            print("\033[96m" + f"{np.array(data[attr]).shape}" + "\033[m")
        else:
            print("\033[96m" + f"{np.array(data[attr]).shape}" + "\033[m")
    texts = convert_recognition_to_text(np.array(data["rec_preds"]))
    boxlist = BoxList(np.array(data["boxes"]), np.array(data["img_size"]))
    print("\033[95m" + f"texts: {texts}" + "\033[m")
    # rec_preds = data["rec_preds"]
    # boxes = data["boxes"]
    # scores = data["scores"]
    # img_size = data["img_size"]
    # print("\033[95m" + f"texts: {rec_preds}" + "\033[m")
    # print("\033[95m" + f"boxes: {boxes}" + "\033[m")
    # print("\033[95m" + f"img_size: {img_size}" + "\033[m")
    # print("\033[95m" + f"scores: {scores}" + "\033[m")
    boxlist.add_field("scores", np.array(data["scores"]))
    boxlist.add_field("texts", texts)
    return boxlist


@router.post("/basic_cert")
async def basic_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_basic_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result.values}, debug_dic: {debug_dic.values}" + "\033[m")
    return {"texts": result}


@router.post("/family_cert")
async def family_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_family_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    # print("\033[95m" + f"texts: {result}, debug_dic: {debug_dic}" + "\033[m")
    return {"texts": result}


@router.post("/rrtable")
async def rrtable(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)

    result, debug_dic = postprocess_rrtable(boxlist, 0.5, [])
    # logger.info(f"Rec inference time: \t{(time.time()) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result.values}, debug_dic: {debug_dic.values}" + "\033[m")

    return {"texts": result}


@router.post("/regi_cert")
async def regi_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    result, debug_dic = postprocess_regi_cert(boxlist)
    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
    print("\033[95m" + f"texts: {result.values}, debug_dic: {debug_dic.values}" + "\033[m")
    return {"texts": result}


# settings = get_settings()
# MODEL_SERVER_URL = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
# PP_SERVER_URL = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"

# image_dir = f"{settings.BASE_PATH}/others/assets/01_0001.png"
# img = cv2.imread(image_dir)
# _, img_encoded = cv2.imencode(".jpg", img)
# img_bytes = img_encoded.tobytes()
# files = {"image": ("document_img.jpg", img_bytes)}


# async def document_ocr_test():
#     async with httpx.AsyncClient() as client:
#         document_ocr_model_response = await client.post(
#             f"{MODEL_SERVER_URL}/document_ocr", files=files, timeout=300.0
#         )
#         document_ocr_result = document_ocr_model_response.json()

#         result = document_ocr_result

#         boxlist = create_boxlist(result)
#         result, _ = postprocess_family_cert(boxlist)
#         return result


# loop = asyncio.get_event_loop()
# loop.run_until_complete(document_ocr_test())
