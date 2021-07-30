import os
import httpx
import uvicorn
import asyncio
import glob

from typing import List, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.datastructures import UploadFile


load_dotenv(find_dotenv())
SERVING_IP_ADDR = os.environ.get("SERVING_IP_ADDR")
SERVING_IP_PORT = os.environ.get("SERVING_IP_PORT")
MODEL_SERVER_URL = f"http://{SERVING_IP_ADDR}:{SERVING_IP_PORT}"

app = FastAPI()


async def request(client, byte_image):
    response = await client.post(f"{MODEL_SERVER_URL}/inference", data=byte_image, timeout=30.0)
    return response.json()


async def task(byte_images, count):
    async with httpx.AsyncClient() as client:
        tasks = [request(client, byte_images[index]) for index in range(count)]
        results = await asyncio.gather(*tasks)
        logger.debug(f"Results: {results}")
        logger.debug(f"Results length: {len(results)}")
        return {"length": len(results), "results": results}


@app.post("/async_test")
async def async_test(offset: int = 0, count: int = 10):
    byte_images = list()
    for index, filename in enumerate(
        glob.glob("/workspace/datasets/val2017/*.jpg")
    ):  # assuming gif
        if len(byte_images) >= count:
            break
        if index <= offset:
            continue
        async with open(filename, "rb") as f:
            data = await f.read()
        await byte_images.append(data)
    response = await task(byte_images, count)
    return JSONResponse(content=jsonable_encoder(response))


@app.post("/inference")
async def Inference(file: UploadFile = File(...)):
    byte_image = await file.read()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MODEL_SERVER_URL}/inference", data=byte_image, timeout=30.0)
        results = response.json()
        return JSONResponse(content=jsonable_encoder(results))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
