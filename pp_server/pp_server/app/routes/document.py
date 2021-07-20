import time
import asyncio
import numpy as np
import sys
import traceback
import pickle

from loguru import logger
from fastapi import Body
from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter

from pp_server.app.common.const import get_settings
from pp_server.app.postprocess.family_cert import postprocess_family_cert
from pp_server.app.postprocess.basic_cert import postprocess_basic_cert
from pp_server.app.postprocess.rrtable import postprocess_rrtable
from pp_server.app.postprocess.regi_cert import postprocess_regi_cert
from pp_server.app.utils.utils import create_boxlist



settings = get_settings()
router = APIRouter()


# logger.info(f"Rec inference time: \t{(time.time()) * 1000:.2f}ms")


@router.post("/basic_cert")
async def basic_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    try:
        result, debug_dic = postprocess_basic_cert(boxlist)
        # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")
    except:
        logger.debug(f"Unexpected error: {sys.exc_info()}")
        logger.debug(traceback.print_exc())
        result = None
    return {"texts": result}


@router.post("/family_cert")
async def family_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    try:
        result, debug_dic = postprocess_family_cert(boxlist)
        # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        logger.info(f"texts: {result}, debug_dic: {debug_dic}")
    except:
        logger.debug(f"Unexpected error: {sys.exc_info()}")
        logger.debug(traceback.print_exc())
        result = None
    return {"texts": result}


@router.post("/rrtable")
async def rrtable(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    try:
        result, debug_dic = postprocess_rrtable(boxlist, 0.5, [])
        logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")
    except:
        logger.debug(f"Unexpected error: {sys.exc_info()}")
        logger.debug(traceback.print_exc())
        result = None
    return {"texts": result}


@router.post("/regi_cert")
async def regi_cert(data: dict = Body(...)) -> Any:
    boxlist = create_boxlist(data)
    try:
        result, debug_dic = postprocess_regi_cert(boxlist)
        logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")
    except:
        logger.debug(f"Unexpected error: {sys.exc_info()}")
        logger.debug(traceback.print_exc())
        result = None
    return {"texts": result}

    # logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")


############################## for debugging ##############################




# with open("/workspace/assets/basic_cert_boxlist_data.pickle", "rb") as fr:
#     saved_data = pickle.load(fr)
# boxlist = create_boxlist(saved_data)
# result, debug_dic = postprocess_basic_cert(boxlist)
# logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")

# with open("/workspace/assets/boxlist_data.pickle", "rb") as fr:
#     saved_data = pickle.load(fr)
# boxlist = create_boxlist(saved_data)
# result, debug_dic = postprocess_regi_cert(boxlist)
# logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")



# with open("/workspace/assets/family_cert_boxlist_data.pickle", "rb") as fr:
#     saved_data = pickle.load(fr)
# boxlist = create_boxlist(saved_data)
# result, debug_dic = postprocess_family_cert(boxlist)
# logger.info(f"texts: {result.values}, debug_dic: {debug_dic.values}")



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
