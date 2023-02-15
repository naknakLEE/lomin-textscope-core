import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from app.service.status import (
    livez as livez_service,
    readyz as readyz_service
)

router = APIRouter()


@router.get("/livez")
async def livez() -> "Response":
    """
    Make sure it works with Kubernetes liveness probe
    """
    return await livez_service()


@router.get("/readyz")
async def readyz() -> "Response":
    return await readyz_service()
