import sys

from io import BytesIO
from minio import Minio, S3Error
from minio.deleteobjects import DeleteObject
from typing import Union, Optional
from app.common.const import get_settings
from app.utils.logging import logger
from pathlib import Path

settings = get_settings()


class MinioService:
    client: Minio

    def __init__(
        self,
        host: str = settings.MINIO_IP_ADDR,
        port: Union[str, int] = settings.MINIO_IP_PORT,
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

    def put(self, object_name: str, bucket_name: str, data: bytes, **kwargs) -> bool:
        if not self._bucket_exists(bucket_name):
            logger.error(f"Error occur for not exist bucket '{bucket_name}'")
            return False
        try:
            length = len(data)
            buffer = BytesIO(data)
            tags:str = kwargs.get('tags', None)
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=buffer,
                length=length,
                tags=tags
            )
            return True
        except S3Error:
            logger.error(f"Error occur for upload image '{object_name}'")
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
    
    def get(self, image_name: str, bucket_name: str) -> Optional[bytes]:
        image_bytes = None
        if not self._bucket_exists(bucket_name):
            logger.error(f"Error occur for not exist bucket '{bucket_name}'")
            return None
        try:
            response = self.client.get_object(bucket_name, image_name)
            image_bytes = response.data
        except S3Error:
            logger.error(f"Error occur for load image '{image_name}'")
            logger.error(f"'{image_name}' is not exists")
        except Exception:
            error = sys.exc_info()
            exc_type, exc_value, exc_traceback = error
            error_log = {
                'filename': exc_traceback.tb_frame.f_code.co_filename,
                'lineno'  : exc_traceback.tb_lineno,
                'name'    : exc_traceback.tb_frame.f_code.co_name,
                'type'    : exc_type.__name__,
                'message' : str(exc_value),
            }
            logger.info("error log detail: {}", error_log)
            del(exc_type, exc_value, exc_traceback, error_log)
        finally:
            if(response):
                response.close()
                response.release_conn()
            return image_bytes
    
    def remove(self, bucket_name: str, image_name: str) -> Optional[bytes]:
        result = False
        if not self._bucket_exists(bucket_name):
            logger.error(f"Error occur for not exist bucket '{bucket_name}'")
            return None
        try:
            self.client.remove_object(bucket_name, image_name)
            result = True
        except S3Error:
            logger.error(f"Error occur for delete image '{image_name}'")
            logger.error(f"'{image_name}' is not exists")
        except Exception:
            error = sys.exc_info()
            exc_type, exc_value, exc_traceback = error
            error_log = {
                'filename': exc_traceback.tb_frame.f_code.co_filename,
                'lineno'  : exc_traceback.tb_lineno,
                'name'    : exc_traceback.tb_frame.f_code.co_name,
                'type'    : exc_type.__name__,
                'message' : str(exc_value),
            }
            logger.info("error log detail: {}", error_log)
            del(exc_type, exc_value, exc_traceback, error_log)
        finally:
            return result

    def remove_(self, bucket_name: str, object_name: str):
        if not self._bucket_exists(bucket_name):
            logger.error(f"Error occur for not exist bucket '{bucket_name}'")
        try:
            delete_object_list = map(
                lambda x: DeleteObject(x.object_name),
                self.client.list_objects(bucket_name, prefix=object_name, recursive=True),
            )
            errors = self.client.remove_objects(bucket_name, delete_object_list)
            for error in errors:
                print("error occured when deleting object", error)

        except S3Error:
            logger.error(f"Error occur for load image '{object_name}'")
            logger.error(f"'{object_name}' is not exists")
        except Exception:
            error = sys.exc_info()
            exc_type, exc_value, exc_traceback = error
            error_log = {
                'filename': exc_traceback.tb_frame.f_code.co_filename,
                'lineno'  : exc_traceback.tb_lineno,
                'name'    : exc_traceback.tb_frame.f_code.co_name,
                'type'    : exc_type.__name__,
                'message' : str(exc_value),
            }
            logger.info("error log detail: {}", error_log)
            del(exc_type, exc_value, exc_traceback, error_log)

    def move_file_to_local_directory(self, bucket_name: str, document_path_list: list, local_directory: str):
        Path(local_directory).mkdir(parents=True, exist_ok=True)

        for document_path in document_path_list:
            file_bytes = self.get(image_name=document_path, bucket_name=bucket_name)
            if(not file_bytes): continue

            try:
                origin_name = document_path.split("/")[-1]
                local_dir = "/".join([local_directory, origin_name])
                with open(local_dir, "wb") as pdf:
                    pdf.write(file_bytes)                
            except Exception:
                error = sys.exc_info()
                exc_type, exc_value, exc_traceback = error
                error_log = {
                    'filename': exc_traceback.tb_frame.f_code.co_filename,
                    'lineno'  : exc_traceback.tb_lineno,
                    'name'    : exc_traceback.tb_frame.f_code.co_name,
                    'type'    : exc_type.__name__,
                    'message' : str(exc_value),
                }
                logger.info("error log detail: {}", error_log)
                del(exc_type, exc_value, exc_traceback, error_log)  