import os

import traceback
import httpx
import base64
import pandas as pd
from typing import Optional, List, Any

from app import hydra_cfg
from app.common.const import get_settings
from app.utils.logging import logger
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()

async def save_bytes_to_nas(file_list:List):
    rpa_cfg = hydra_cfg.common.rpa
    nas_path = rpa_cfg.save_nas_path
    file_name_separator = rpa_cfg.file_name_separator
    
    upload_file_name = []
    for file_name, bytes_data in file_list:
        # 파일 있으면 파일 저장
        try:
            
            document_save_path = os.path.join(nas_path, file_name)
            logger.info(f"save bytes to nas : {document_save_path}")
            if not os.path.exists(nas_path):
                os.makedirs(nas_path)
            with open(document_save_path, "wb") as file:
                file.write(bytes_data)
            upload_file_name.append(file_name)
        except Exception as ex:
            traceback.print_exc()
            raise CoreCustomException("C01.002.5001")
    upload_file_name = file_name_separator.join(upload_file_name)
    return upload_file_name

async def send_rpa(
    send_mail_addr: str,
    to_mail_addr: str = "",
    cc_mail_addr: str = "",
    bcc_mail_addr: str = "",
    subject_title: str = "",
    body_data: str = "",
    upload_file_list: list = [],
    append_file_list: list = []
    
):
    rpa_cfg = hydra_cfg.common.rpa
    rpa_ip = rpa_cfg.rpa_ip
    rpa_port = rpa_cfg.rpa_port
    rpa_url = rpa_cfg.rpa_url
    
    upload_file_name = await save_bytes_to_nas(upload_file_list)
    append_file_name = await save_bytes_to_nas(append_file_list)
    
        
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"http://{rpa_ip}:{rpa_port}{rpa_url}",
                json={
                    "send_mail_addr": send_mail_addr,
                    "to_mail_addr": to_mail_addr,
                    "cc_mail_addr": cc_mail_addr,
                    "bcc_mail_addr": bcc_mail_addr,
                    "subject_title": subject_title,
                    "body_data": body_data,
                    "upload_file_name": upload_file_name,
                    "append_file_name": append_file_name
                    
                },
                timeout=settings.TIMEOUT_SECOND,
            )
    except:
        raise CoreCustomException("C01.006.5001")
    