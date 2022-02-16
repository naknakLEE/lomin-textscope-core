import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response


router = APIRouter()


@router.get("/livez")
async def livez() -> "Response":
    """
    Make sure it works with Kubernetes liveness probe
    """
    return PlainTextResponse("\n", status_code=200)


@router.get("/readyz")
async def readyz() -> "Response":
    if os.getenv("IS_READY") == "true":
        return PlainTextResponse("\n", status_code=200)
    raise HTTPException(500)
