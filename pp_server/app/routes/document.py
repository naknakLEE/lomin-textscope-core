import aiohttp
import requests
import time
import asyncio
import json
import io
import struct
import cv2
import httpx


from typing import List
from fastapi.responses import StreamingResponse
from fastapi.datastructures import UploadFile
from fastapi import Body
from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, File
from fastapi.requests import Request
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.responses import Response
from inspect import currentframe as frame

from app.database.connection import db
from app.database.schema import Users, Usage, Logs
from app.common.const import get_settings
from app import models


settings = get_settings()
router = APIRouter()
# # redis_cache = Redis(host=settings.REDIS_IP_ADDR, port=settings.REDIS_IP_PORT, db=0)
# serving_server_inference_url = (
#     f"http://182.20.0.4:8080/inference"
# )


@router.post("/pp/detection")
async def inference(data: dict = Body(...)) -> Any:
    boxes = data["boxes"]
    # await asyncio.sleep(2)

    # print("\033[94m" + f"1: {boxes}" + "\033[m")
    return {"boxes": boxes}


@router.post("/pp/recognition")
async def inference(data: dict = Body(...)) -> Any:
    string = data["string"]
    # await asyncio.sleep(2)

    # print("\033[94m" + f"2: {string}" + "\033[m")
    return {"string": string}


# fake_db = {}

# async def fromRedis(r,n):
#    """Retrieve Numpy array from Redis key 'n'"""
#    encoded = await r.get(n)
#    h, w = struct.unpack('>II',encoded[:8])
#    # Add slicing here, or else the array would differ from the original
#    a = np.frombuffer(encoded[8:], dtype=np.uint8).reshape(h,w,3)
#    return a

# def toRedis(r,a,n):
#    """Store given Numpy array 'a' in Redis under key 'n'"""
#    h, w, _ = a.shape
#    shape = struct.pack('>II',h,w)
#    encoded = shape + a.tobytes()

#    # Store encoded data in Redis
#    r.set(n,encoded)
#    return

# @router.post("/stage1")
# async def inference(image_name: str) -> Any:
#     image = fromRedis(redis_cache, image_name)
#     # print('\033[36m' + f"postprocessing stage1 image shape: {image.shape}" + '\033[m')
#     # await asyncio.sleep(1)
#     print('\033[36m' + f"postprocessing stage1 image shape: {image.shape}" + '\033[m')
#     """
#     Required post-processing code
#     """
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_inference_url}/stage2?image_name={image_name}",
#         ) as response:
#             result = await response.json()
#             print('\033[36m' + f"postprocessing stage1 result: {result}" + '\033[m')
#             return result


# @router.post("/stage2")
# async def inference(image_name: str) -> Any:
#     image = await fromRedis(redis_cache, image_name)
#     # print('\033[36m' + f"postprocessing stage2 image shape: {image.shape}" + '\033[m')
#     # """
#     # Required post-processing code
#     # """

#     print('\033[36m' + f"postprocessing complete" + '\033[m')
#     return image.shape


# # @router.post("/stage3")
# # async def inference(image_name: str) -> Any:
# #     image = fromRedis(redis_cache, image_name)
# #     print('\033[36m' + f"postprocessing stage3 image shape: {image.shape}" + '\033[m')
# #     """
# #     Required post-processing code
# #     """
# #     print('\033[36m' + f"postprocessing complete" + '\033[m')
# #     return image_name


# @router.post("/receive_from_http")
# async def inference(encoded: UploadFile = File(...)) -> Any:
#     # encoded = await encoded.read()
#     # h, w = struct.unpack('>II',encoded[:8])
#     # # Add slicing here, or else the array would differ from the original
#     # image = np.frombuffer(encoded[8:], dtype=np.uint8).reshape(h,w,3)
#     # # encoded_img = np.frombuffer(image, dtype=np.uint8)
#     # # img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

#     # # print('\033[94m' + f"{img.shape}" + '\033[m')
#     # # res, encoded_img = cv2.imencode('.jpg', img)
#     # # return StreamingResponse(io.BytesIO(encoded_img.tobytes()), media_type="image/png")
#     # h, w, _ = image.shape
#     # shape = struct.pack('>II',h,w)
#     # encoded = shape + image.tobytes()
#     # return encoded
#     # return Response(encoded, media_type="image/png")
#     return 1234
#     # serving_server_inference_url = (
#     #     f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference"
#     # )

#     # image_data = await file.read()
#     # async with aiohttp.ClientSession() as session:
#     #     async with session.post(
#     #         serving_server_inference_url, data=image_data
#     #     ) as response:
#     #         result = await response.json()
#     #         return models.InferenceResponse(ocrResult=result)
