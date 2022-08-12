import httpx
import os
import base64
from pathlib import Path

from app import hydra_cfg
from app.common.const import get_settings
from app.utils.logging import logger
from app.middlewares.exception_handler import CoreCustomException

settings = get_settings()

def document_path_verify(document_path: str):
    if not os.path.isfile(document_path):
        raise CoreCustomException(2508)
    return True

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

    async def file_nas_share(self, base64_data: str, file_name: str, url: str, drm_user: str) -> str:
        try:
            document_save_path = os.path.join(self.save_path, file_name)
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
            with open(document_save_path, 'wb') as f:
                f.write(base64.b64decode(base64_data))
        except Exception as ex:
            raise CoreCustomException("C01.002.5001")
        
        input_params = {
                        "from_file_nm": file_name,
                        "to_file_nm": file_name,
                        "drm_user": drm_user
                    }
        logger.info(f"drm request ip: http://{self.drm_ip}:{self.drm_port}{url}")
        logger.info(f"drm request input params: {input_params}")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"http://{self.drm_ip}:{self.drm_port}{url}",
                    json=input_params,
                    timeout=settings.TIMEOUT_SECOND,
                )
                logger.info(f"response status_code : {res.status_code}, response json: {res.json()}")
        except:
            raise CoreCustomException("C01.006.5001")
    
        status_code = res.status_code
        response_data = res.json()
        if int(response_data.get("status")) == 9999:
            logger.error("암호화 해제중 에러가 발생하였습니다.")
        
        load_path = os.path.join(self.get_path, file_name)
        base64_data = load_file2base64(load_path)
        return base64_data
    
    async def drm_encryption(self, base64_data: str, file_name: str, drm_user: str, encryption_url: str = None) -> str:
        if not encryption_url:
            encryption_url = self.nas_encryption_url
        base64_data = await self.file_nas_share(base64_data, file_name, encryption_url, drm_user)
        return base64_data
        
        
    async def drm_decryption(self, base64_data: str, file_name: str, drm_user: str, decryption_url: str = None) -> str:
        if not decryption_url:
            decryption_url = self.nas_decryption_url
        base64_data = await self.file_nas_share(base64_data, file_name, decryption_url, drm_user)
        return base64_data
    