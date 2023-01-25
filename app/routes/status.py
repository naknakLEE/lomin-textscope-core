from fastapi import APIRouter
from fastapi.responses import Response
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
