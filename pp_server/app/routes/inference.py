# import aiohttp
# import requests
# import time
# import asyncio
# import numpy as np
# import base64
# import json
# import cv2
# import io
# import struct
# import array

# from typing import List
# from multiprocessing import shared_memory
# from redis import Redis
# from fastapi.responses import StreamingResponse
# from fastapi.datastructures import UploadFile
# from fastapi import Body
# from typing import Any
# from datetime import datetime
# from fastapi import APIRouter, Depends, File
# from fastapi.requests import Request
# from sqlalchemy.orm import Session
# from fastapi.responses import JSONResponse
# from starlette.responses import Response
# from inspect import currentframe as frame

# from app.database.connection import db
# from app.database.schema import Users, Usage, Logs
# from app.common.const import get_settings
# from app import models

# # from pp_server.app.database.connection import redis_cache


# settings = get_settings()
# router = APIRouter()
# redis_cache = Redis(host=settings.REDIS_IP_ADDR, port=settings.REDIS_IP_PORT, db=0)
# # shm_a = shared_memory.SharedMemory(create=True, size=40000000)
# serving_server_postprocessing_url = f"http://182.20.0.4:8080/postprocessing"


# async def toRedis(r, a, n):
#     """Store given Numpy array 'a' in Redis under key 'n'"""
#     h, w, _ = a.shape
#     shape = struct.pack(">II", h, w)
#     encoded = a.tobytes()

#     # Store encoded data in Redis
#     r.set(n, encoded)
#     return


# async def fromRedis(r, n):
#     """Retrieve Numpy array from Redis key 'n'"""
#     encoded = r.get(n)
#     h, w = struct.unpack(">II", encoded[:8])
#     # Add slicing here, or else the array would differ from the original
#     a = np.frombuffer(encoded[8:], dtype=np.uint8).reshape(h, w, 3)
#     return a


# @router.post("/redis_test")
# async def inference(file: UploadFile = File(...)) -> Any:
#     byte_image_data = await file.read()
#     encoded_img = np.frombuffer(byte_image_data, dtype=np.uint8)
#     image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

#     print("\033[93m" + f"start inference: {image.shape}" + "\033[m")
#     start = time.time()
#     image_name = start
#     """
#     Required inference code
#     """
#     await toRedis(redis_cache, image, image_name)

#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_postprocessing_url}/stage2?image_name={image_name}",
#         ) as response:
#             # result = await response.json()
#             result = await response.read()
#             redis_cache.delete(image_name)
#             # encoded_img = np.frombuffer(result, dtype=np.uint8)
#             # img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
#             print("\033[93m" + f"{result}" + "\033[m")
#             end = time.time()
#             print("\033[93m" + f"total time: {end-start}" + "\033[m")
#     # image = await fromRedis(redis_cache, image_name)
#     # return image.shape


# @router.post("/start_stage")
# async def inference(file: UploadFile = File(...)) -> Any:
#     byte_image_data = await file.read()
#     encoded_img = np.frombuffer(byte_image_data, dtype=np.uint8)
#     image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

#     print("\033[93m" + f"start inference: {image.shape}" + "\033[m")
#     start = time.time()
#     image_name = start
#     """
#     Required inference code
#     """
#     toRedis(redis_cache, image, image_name)

#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_postprocessing_url}/stage1?image_name={image_name}",
#         ) as response:
#             result = await response.json()
#             redis_cache.delete(image_name)
#             # encoded_img = np.frombuffer(result, dtype=np.uint8)
#             # img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
#             print("\033[93m" + f"{result}" + "\033[m")
#             end = time.time()
#             print("\033[93m" + f"total time: {end-start}" + "\033[m")


# @router.post("/stage2")
# async def inference(image_name: str) -> Any:
#     image = fromRedis(redis_cache, image_name)
#     print("\033[93m" + f"inference stage2 image shape: {image.shape}" + "\033[m")
#     """
#     Required inference code
#     """
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_postprocessing_url}/stage2?image_name={image_name}",
#         ) as response:
#             result = await response.json()
#             print("\033[36m" + f"inference stage2 result: {result}" + "\033[m")
#             return result


# @router.post("/stage3")
# async def inference(image_name: str) -> Any:
#     image = fromRedis(redis_cache, image_name)
#     print("\033[93m" + f"inference stage3 image shape: {image.shape}" + "\033[m")
#     """
#     Required inference code
#     """
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_postprocessing_url}/stage3?image_name={image_name}",
#         ) as response:
#             result = await response.json()
#             print("\033[36m" + f"inference stage3 result: {result}" + "\033[m")
#             return result


# @router.post("/send_to_http")
# async def inference(file: UploadFile = File(...)) -> Any:
#     byte_image_data = await file.read()
#     # encoded_img = np.frombuffer(byte_image_data, dtype=np.uint8)
#     # image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

#     # print('\033[94m' + f"{image.shape}" + '\033[m')
#     # start = time.time()
#     # image_name = start

#     # h, w, _ = image.shape
#     # shape = struct.pack('>II',h,w)
#     # encoded = shape + image.tobytes()

#     data = {"encoded": byte_image_data}

#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             f"{serving_server_postprocessing_url}/receive_from_http", data=data
#         ) as response:
#             result = await response.json()
#             # h, w = struct.unpack('>II',result[:8])
#             # # Add slicing here, or else the array would differ from the original
#             # a = np.frombuffer(result[8:], dtype=np.uint8).reshape(h,w,3)
#             print("\033[94m" + f"{result}" + "\033[m")
#             # end = time.time()
#             # print('\033[94m' + f"total time: {end-start}" + '\033[m')


# @router.post("/stage_one")
# async def inference(image: UploadFile = File(...)) -> Any:
#     image = await image.read()
#     encoded_img = np.frombuffer(image, dtype=np.uint8)
#     image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
#     print("\033[94m" + f"1: {image.shape}" + "\033[m")
#     return image.shape


# @router.post("/stage_two")
# async def inference(boxes: List[int]) -> Any:
#     # print("\033[94m" + f"1: {boxes}" + "\033[m")
#     return boxes


# @router.post("/stage_three")
# async def inference(string: List[str]) -> Any:
#     print("\033[94m" + f"2: {string}" + "\033[m")
#     return string
