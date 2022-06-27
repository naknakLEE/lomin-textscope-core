import os
import tifffile
import pdf2image
import base64

from datetime import datetime
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Tuple
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from typing import Dict


from app.utils.logging import logger
from app.common.const import get_settings
from app.utils.minio import MinioService
from app.schemas import error_models as ErrorResponse



settings = get_settings()
minio_client = MinioService()
support_file_extension_list = {
    "image": [".jpg", ".jpeg", ".jp2", ".png", ".bmp"],
    "tif": [".tif", ".tiff"],
    "pdf": [".pdf"]
}


def get_file_extension(document_filename: str = "x.xxx") -> str:
    return Path(document_filename).suffix.lower()

@lru_cache(maxsize=15)
def get_page_count(document_data: str, document_filename: str) -> int:
    document_bytes = base64.b64decode(document_data)
    file_extension = get_file_extension(document_filename)
    total_pages = 1
    
    if file_extension in support_file_extension_list.get("image"):
        total_pages = 1
        
    elif file_extension in support_file_extension_list.get("tif"):
        try:
            with tifffile.TiffFile(BytesIO(document_bytes)) as tif:
                total_pages = len(tif.pages)
        except:
            logger.exception("read pillow")
            logger.error(f"Cannot load {document_filename}")
            total_pages = 0
            
    elif file_extension in support_file_extension_list.get("pdf"):
        pages = pdf2image.convert_from_bytes(document_bytes)
        total_pages = len(pages)
        
    else:
        logger.error(f"{document_filename} is not supported!")
        total_pages = 0
    
    return total_pages


def is_support_format(document_filename: str) -> bool:
    file_extension = get_file_extension(document_filename)
    support = False
    
    for support_list in support_file_extension_list.values():
        if file_extension in support_list:
            support = True
    
    return support


def save_upload_document(
    documnet_id: str, documnet_name: str, documnet_base64: str
) -> Tuple[bool, Path]:
    
    decoded_image_data = base64.b64decode(documnet_base64)
    success = False
    save_path = ""
    if settings.USE_MINIO:
        success = minio_client.put(
            bucket_name=settings.MINIO_IMAGE_BUCKET,
            object_name=documnet_id + '/' + documnet_name,
            data=decoded_image_data,
        )
        save_path = "minio/" + documnet_name
        
    else:
        root_path = Path(settings.IMG_PATH)
        base_path = root_path.joinpath(documnet_id)
        base_path.mkdir(parents=True, exist_ok=True)
        save_path = base_path.joinpath(documnet_name)
        
        with save_path.open("wb") as file:
            file.write(decoded_image_data)
        
        success = True
    
    return success, save_path


def document_path_verify(document_path: str):
    if not os.path.isfile(document_path):
        status_code, error = ErrorResponse.ErrorCode.get(2508)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return True
    
    