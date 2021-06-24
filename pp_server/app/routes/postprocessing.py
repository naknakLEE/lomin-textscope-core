import aiohttp
import requests
import time
import asyncio
import numpy as np
import base64
import json
import cv2
import io
import struct


from multiprocessing import shared_memory
from redis import Redis
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
redis_storage = Redis(host=settings.REDIS_IP_ADDR, port=settings.REDIS_IP_PORT, db=0)
serving_server_inference_url = (
    f"http://182.20.0.4:8080/inference"
)


fake_db = {}

def fromRedis(r,n):
   """Retrieve Numpy array from Redis key 'n'"""
   encoded = r.get(n)
   h, w = struct.unpack('>II',encoded[:8])
   # Add slicing here, or else the array would differ from the original
   a = np.frombuffer(encoded[8:], dtype=np.uint8).reshape(h,w,3)
   return a


@router.post("/stage1")
async def inference(image_name: str) -> Any:
    image = fromRedis(redis_storage, image_name)
    print('\033[36m' + f"postprocessing stage1 image shape: {image.shape}" + '\033[m')
    """
    Required post-processing code
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_inference_url}/stage2?image_name={image_name}", 
        ) as response:
            result = await response.json()
            print('\033[36m' + f"postprocessing stage1 result: {result}" + '\033[m')
            return result
    

@router.post("/stage2")
async def inference(image_name: str) -> Any:
    image = fromRedis(redis_storage, image_name)
    print('\033[36m' + f"postprocessing stage2 image shape: {image.shape}" + '\033[m')
    """
    Required post-processing code
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_inference_url}/stage3?image_name={image_name}", 
        ) as response:
            result = await response.json()
            print('\033[36m' + f"postprocessing stage2 result: {result}" + '\033[m')
            return result


@router.post("/stage3")
async def inference(image_name: str) -> Any:
    image = fromRedis(redis_storage, image_name)
    print('\033[36m' + f"postprocessing stage3 image shape: {image.shape}" + '\033[m')
    """
    Required post-processing code
    """
    print('\033[36m' + f"postprocessing complete" + '\033[m')
    return image_name