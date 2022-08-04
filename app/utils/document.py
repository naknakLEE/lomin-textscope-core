import os
import tifffile
import pdf2image
import base64

import httpx
from datetime import datetime
from PIL import Image
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

def load_file2base64(file_path: str):
    file_path = Path(file_path)
    document_name = file_path.name
    path_verify = document_path_verify(file_path)
    
    with file_path.open('rb') as file:
        document_data = file.read()
    document_data = base64.b64encode(document_data)
    
    return document_data

class DRM:
    def __init__(self) -> None:
        
        drm_cfg = hydra_cfg.common.drm
        self.save_path = drm_cfg.save_path
        self.get_path = drm_cfg.get_path
        self.drm_ip = drm_cfg.drm_ip
        self.drm_port = drm_cfg.drm_port
        self.nas_decryption_url = drm_cfg.nas_decryption_url
        self.nas_encryption_url = drm_cfg.nas_encryption_url

    async def file_nas_share(self, base64_data: str, file_name: str, url: str) -> str:
        try:
            document_save_path = os.path.join(self.save_path, file_name)
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
            with open(document_save_path, 'wb') as f:
                f.write(base64.b64decode(base64_data))
        except Exception as ex:
            raise CoreCustomException("C01.002.5001")
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"http://{self.drm_ip}:{self.drm_port}{url}",
                    json={
                        "from_file_nm": file_name,
                        "to_file_nm": file_name
                    },
                    timeout=settings.TIMEOUT_SECOND,
                )
        except:
            raise CoreCustomException("C01.006.5001")
    
        status_code = res.status_code
        response_data = res.json()
        if int(response_data.get("status")) == 9999:
            logger.error("암호화 해제중 에러가 발생하였습니다.")
        
        load_path = os.path.join(self.get_path, file_name)
        base64_data = load_file2base64(load_path)
        return base64_data
    
    async def drm_encryption(self, base64_data: str, file_name: str, encryption_url: str = None) -> str:
        if not encryption_url:
            encryption_url = self.nas_encryption_url
        base64_data = await self.file_nas_share(base64_data, file_name, encryption_url)
        return base64_data
        
        
    async def drm_decryption(self, base64_data: str, file_name: str, decryption_url: str = None) -> str:
        if not decryption_url:
            decryption_url = self.nas_decryption_url
        base64_data = await self.file_nas_share(base64_data, file_name, decryption_url)
        return base64_data
        

def save_upload_document(
    documnet_id: str, documnet_name: str, documnet_base64: str, /, separate: bool = False
) -> Tuple[bool, Path]:
    
    decoded_image_data = base64.b64decode(documnet_base64)
    
    save_document_dict = dict()
    
    # 원본 파일
    save_document_dict.update({'/'.join([documnet_id, documnet_name]): decoded_image_data})
    
    # 장 단위 분리
    if separate:
        document_pages: List[Image.Image] = read_image_from_bytes(decoded_image_data, documnet_name, 0.0, 1, separate=separate)
        for page, document_page in enumerate(document_pages):
            buffered = BytesIO()
            document_page.save(buffered, "png")
            
            save_document_dict.update({'/'.join([documnet_id, str(page+1)+".png"]): buffered.getvalue()})
    
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
    
    return success, save_path


def document_path_verify(document_path: str):
    if not os.path.isfile(document_path):
        raise CoreCustomException(2508)
    return True


def get_document_bytes(document_id: str, document_path: Path) -> str:
    document_bytes = None
    
    if settings.USE_MINIO:
        image_minio_path = "/".join([document_id, document_path.name])
        document_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET)
    else:
        with document_path.open("rb") as f:
            document_bytes = f.read()
    
    return document_bytes