import aiohttp
from fastapi.applications import FastAPI
import requests
import time
import asyncio
import numpy as np
import base64
import json
import cv2
import io
import struct
import requests

from starlette.testclient import TestClient
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

from pp_server.app.database.connection import redis_cache


settings = get_settings()
router = APIRouter()
# redis_cache = Redis(host=settings.REDIS_IP_ADDR, port=settings.REDIS_IP_PORT, db=0)
serving_server_url = f"http://182.20.0.4:8080"
web_server_url = f"http://182.20.0.5:8000"

app = FastAPI()

client = TestClient(app)


@router.post("/pipeline")
async def inference(image: UploadFile = File(...)) -> Any:
    image_bytes = await image.read()
    image = {"image": image_bytes}

    # Detection
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_url}/inference/stage_one", data=image
        ) as response:
            result = await response.json()
            boxes = result
            print("\033[94m" + f"{result}" + "\033[m")

    # Post-Processing 1
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_url}/inference/stage_one", data=image
        ) as response:
            result = await response.json()
            boxes = result
            print("\033[94m" + f"{result}" + "\033[m")

    # Recognition
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_url}/inference/stage_two", json=boxes
        ) as response:
            result = await response.json()
            string = result
            print("\033[94m" + f"{result}" + "\033[m")

    # Post-Processing 2: result
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{serving_server_url}/inference/stage_one", data=image
        ) as response:
            result = await response.json()
            return result
