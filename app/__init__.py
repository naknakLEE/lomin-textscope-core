from minio import Minio
from app.common.const import get_settings


settings = get_settings()


mc = Minio(
    "{}:{}".format(settings.MINIO_IP_ADDR, settings.MINIO_PORT),
    secure=False,
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
)
if not mc.bucket_exists(settings.MINIO_IMAGE_BUCKET):
    mc.make_bucket(settings.MINIO_IMAGE_BUCKET)


__all__ = [
    "mc"
]