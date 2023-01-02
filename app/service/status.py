import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response


async def livez() -> "Response":
    """
    Make sure it works with Kubernetes liveness probe
    """
    return PlainTextResponse("\n", status_code=200)


async def readyz() -> "Response":
    if os.getenv("IS_READY") == "true":
        return PlainTextResponse("\n", status_code=200)
    raise HTTPException(500)
