import os

import httpx
import base64
import pandas as pd

from app.common.const import get_settings
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()

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
    nas_path = "/workspace/data/file_attach"
    rpa_ip = "textscope-web"
    rpa_port = "8000"
    rpa_url = "/test/rpa/sendDwpMail"
    
    upload_file_name = []
    for file_name, pd_xlsx in upload_file_list:
        # 파일 있으면 파일 저장
        try:
            document_save_path = os.path.join(nas_path, file_name)
            if not os.path.exists(nas_path):
                os.makedirs(nas_path)
            with open(document_save_path, "wb") as file:
                file.write(pd_xlsx)
            upload_file_name.append(file_name)
        except Exception as ex:
            raise CoreCustomException("C01.002.5001")
    upload_file_name = "||".join(upload_file_name)
    
    append_file_name = []
    for file_name, pd_xlsx in append_file_list:
        # 파일 있으면 파일 저장
        try:
            document_save_path = os.path.join(nas_path, file_name)
            if not os.path.exists(nas_path):
                os.makedirs(nas_path)
            with open(document_save_path, "wb") as file:
                file.write(pd_xlsx)
            append_file_name.append(file_name)
        except Exception as ex:
            raise CoreCustomException("C01.002.5001")
    append_file_name = "||".join(append_file_name)
        
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
                timeout=10,
            )
    except:
        raise CoreCustomException("C01.006.5001")
    