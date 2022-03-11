import sys

from io import BytesIO
from minio import Minio, S3Error
from typing import Union
from app.common.const import get_settings
from app.utils.logging import logger

settings = get_settings()


class MinioService:
    client: Minio

    def __init__(
        self,
        host: str = settings.MINIO_IP_ADDR,
        port: Union[str, int] = settings.MINIO_PORT,
        secure: bool = settings.MINIO_USE_SSL,
    ) -> None:
        if isinstance(secure, str):
            secure = True if secure.lower() == "true" else False
        self.client = Minio(
            f"{host}:{port}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=secure,
        )

    def _bucket_exists(self, bucket_name: str) -> bool:
        return self.client.bucket_exists(bucket_name)

    def put(self, object_name: str, bucket_name: str, data: bytes) -> bool:
        if not self._bucket_exists(bucket_name):
            logger.error(f"Error occur for not exist bucket '{bucket_name}'")
            return False
        try:
            length = len(data)
            buffer = BytesIO(data)
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=buffer,
                length=length,
            )
            return True
        except S3Error:
            logger.error(f"Error occur for load image '{object_name}'")
            logger.error(f"'{object_name}' is not exists")
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if (
                exc_type is not None
                and exc_value is not None
                and exc_traceback is not None
            ):
                error_log = {
                    "filename": exc_traceback.tb_frame.f_code.co_filename,
                    "lineno": exc_traceback.tb_lineno,
                    "name": exc_traceback.tb_frame.f_code.co_name,
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                }
                logger.info("error log detail: {}", error_log)
                del (exc_type, exc_value, exc_traceback, error_log)
        return False
