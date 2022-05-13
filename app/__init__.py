from minio import Minio
from app.common.const import get_settings
from os import environ
from pathlib import Path, PurePath
from hydra import initialize_config_dir, compose


settings = get_settings()

base_dir = Path(__file__).resolve().parent.parent
initialize_config_dir(config_dir=environ.get(
    "CONFIG_DIR",
    PurePath("/", "workspace", "app", "assets", "conf").as_posix()
    )
) 
hydra_cfg = compose(config_name='config')


mc = Minio(
    "{}:{}".format(settings.MINIO_IP_ADDR, settings.MINIO_IP_PORT),
    secure=False,
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
)
if not mc.bucket_exists(settings.MINIO_IMAGE_BUCKET):
    mc.make_bucket(settings.MINIO_IMAGE_BUCKET)


__all__ = [
    "mc",
    "hydra_cfg"
]