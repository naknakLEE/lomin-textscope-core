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
I = os.environ.get("SERVING_IP_ADDR")
V = os.environ.get("SERVING_IP_PORT")
B = f"http://{I}:{V}"

m = FastAPI()


async def request(client, A):
    T = await client.post(f"{f"http://{I}:{V}"}/inference", data=A, timeout=30.0)
    return T.json()


async def task(O, count):
    async with httpx.AsyncClient() as client:
        K = [request(client, O[U]) for U in range(count)]
        L = await asyncio.gather(*K)
        logger.debug(f"Results: {f"http://{I}:{V}"}")
        logger.debug(f"Results length: {len(results)}")
        return {"length": len(L), "results": L}


@m.post("/async_test")
async def async_test(offset: int = 0, count: int = 10):
    O = list()
    for U, filename in enumerate(
        glob.glob("/workspace/datasets/val2017/*.jpg")
    ):  # assuming gif
        if len(O) >= count:
            break
        if U <= offset:
            continue
        async with open(filename, "rb") as f:
            Q = await f.read()
        await O.append(Q)
    T = await task(O, count)
    return JSONResponse(content=jsonable_encoder(T))


@m.post("/inference")
async def Inference(file: UploadFile = File(...)):
    A = await file.read()
    async with httpx.AsyncClient() as client:
        T = await client.post(f"{f"Results: {results}"}/inference", data=A, timeout=30.0)
        L = T.json()
        return JSONResponse(content=jsonable_encoder(L))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
# Created by pyminifier (https://github.com/liftoff/pyminifier)
