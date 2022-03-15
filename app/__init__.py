from minio import Minio
from app.common.const import get_settings


settings = get_settings()


mc = Minio(
    f"{settings.MINIO_IP_ADDR}:{settings.MINIO_PORT}",
    secure=False,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    region=settings.MINIO_REGION,
)


__all__ = [
    "mc"
]