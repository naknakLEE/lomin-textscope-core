import os
import uvicorn

from minio import Minio
from app.common.const import get_settings
from app.utils.create_app import app_generator

os.environ["API_ENV"] = "production"

settings = get_settings()

app = app_generator()
args = {
    "app": "main:app",
    "host": "0.0.0.0",
    "port": 80,
    "workers": settings.TEXTSCOPE_CORE_WORKERS,
}
if settings.DEVELOP:
    args["reload"] = True


# class MyManager(SyncManager):
#     pass


# syncdict = {}


# def get_dict():
#     return syncdict

if settings.USE_MINIO:
    mc = Minio(
        f"{settings.MINIO_IP_ADDR}:{settings.MINIO_PORT}",
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=False,
    )
    if not mc.bucket_exists(settings.MINIO_IMAGE_BUCKET):
        mc.make_bucket(settings.MINIO_IMAGE_BUCKET)

if __name__ == "__main__":
    # MyManager.register("syncdict", get_dict)
    # manager = MyManager(("0.0.0.0", 12200), authkey=b"password")
    # manager.start()
    uvicorn.run(**args)
