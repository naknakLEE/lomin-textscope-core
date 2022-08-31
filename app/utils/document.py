import os
import tifffile
import pdf2image
import base64

import httpx
from datetime import datetime
from PIL import Image
from PIL.Image import DecompressionBombError
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Tuple, List
from fastapi.encoders import jsonable_encoder

from app import hydra_cfg
from app.utils.logging import logger
from app.common.const import get_settings
from app.utils.minio import MinioService
from app.utils.image import read_image_from_bytes
from app.schemas import error_models as ErrorResponse
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()
minio_client = MinioService()
support_file_extension_list = {
    "image": [".jpg", ".jpeg", ".jp2", ".png", ".bmp"],
    "tif": [".tif", ".tiff"],
    "pdf": [".pdf"]
}


def get_file_extension(document_filename: str = "x.xxx") -> str:
    return Path(document_filename).suffix.lower()


def get_stored_file_extension(document_path: str) -> str:
    stored_ext = Path(document_path).suffix
    doc_ext = stored_ext
    
    if doc_ext.lower() in settings.MULTI_PAGE_DOCUMENT:
        stored_ext = settings.MULTI_PAGE_SEPARATE_EXTENSION
    
    return stored_ext


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
    documnet_id: str, documnet_name: str, documnet_base64: str, /,  new_document: bool = True
) -> Tuple[bool, Path, int]:
    
    document_extension = Path(documnet_name).suffix
    
    save_document_dict = dict()
    decoded_image_data = base64.b64decode(documnet_base64)
    
    # 원본 파일
    save_document_dict.update({'/'.join([documnet_id, documnet_name]): decoded_image_data})
    
    # pdf나 tif, tiff 일 경우 장 단위 분리
    if document_extension.lower() in settings.MULTI_PAGE_DOCUMENT:
        buffered = BytesIO()
        
        try:
            document_pages: List[Image.Image] = read_image_from_bytes(decoded_image_data, documnet_name, 0.0, 1, separate=True)
        except DecompressionBombError:
            raise CoreCustomException("C01.003.401A")
        
        for page, document_page in enumerate(document_pages):
            document_page.save(buffered, settings.MULTI_PAGE_SEPARATE_EXTENSION[1:])
            save_document_dict.update({'/'.join([documnet_id, str(page+1)+settings.MULTI_PAGE_SEPARATE_EXTENSION]): buffered.getvalue()})
            buffered.seek(0)
    elif new_document:
        save_document_dict.update({'/'.join([documnet_id, "1" + document_extension]): decoded_image_data})
    
    success = True
    save_path = ""
    if settings.USE_MINIO:
        for object_name, data in save_document_dict.items():
            success &= minio_client.put(
                bucket_name=settings.MINIO_IMAGE_BUCKET,
                object_name=object_name,
                data=data,
            )
        save_path = "minio/" + documnet_name
        
    else:
        root_path = Path(settings.IMG_PATH)
        base_path = root_path.joinpath(documnet_id)
        base_path.mkdir(parents=True, exist_ok=True)
        
        for object_name, data in save_document_dict.items():
            save_path = base_path.joinpath(object_name)
            
            with save_path.open("wb") as file:
                file.write(data)
        
        success = True
    
    return success, save_path, (len(save_document_dict) - 1)


def get_document_bytes(document_id: str, document_path: Path) -> str:
    document_bytes = None
    
    if settings.USE_MINIO:
        image_minio_path = "/".join([document_id, document_path.name])
        document_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET)
    else:
        with document_path.open("rb") as f:
            document_bytes = f.read()
    
    return document_bytes