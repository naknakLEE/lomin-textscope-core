import os

import traceback
import httpx
import base64
import pandas as pd
from typing import Optional, List, Any
from sqlalchemy.orm import Session

from app.database import query, schema
from app import hydra_cfg
from app.common.const import get_settings
from app.utils.logging import logger
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()



async def save_bytes_to_nas(file_list:List, save_file_path: str = None):
    rpa_cfg = hydra_cfg.common.rpa
    if not save_file_path:
        save_file_path = rpa_cfg.save_nas_path
    file_name_separator = rpa_cfg.file_name_separator
    upload_file_name = []
    for file_name, bytes_data in file_list:
        # 파일 있으면 파일 저장
        try:
            
            document_save_path = os.path.join(save_file_path, file_name)
            logger.info(f"save bytes to nas : {document_save_path}")
            if not os.path.exists(save_file_path):
                os.makedirs(save_file_path)
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
    nas_file_path: str = "",
    upload_file_list: list = [],
    append_file_list: list = []
    
    
):
    rpa_cfg = hydra_cfg.common.rpa
    rpa_ip = rpa_cfg.rpa_ip
    rpa_port = rpa_cfg.rpa_port
    rpa_url = rpa_cfg.rpa_url
    
    upload_file_name = await save_bytes_to_nas(upload_file_list, nas_file_path)
    append_file_name = await save_bytes_to_nas(append_file_list, nas_file_path)
    
    input_params = {
                    "send_mail_addr": send_mail_addr,
                    "to_mail_addr": to_mail_addr,
                    "cc_mail_addr": cc_mail_addr,
                    "bcc_mail_addr": bcc_mail_addr,
                    "subject_title": subject_title,
                    "body_data": body_data,
                    "nas_file_path": nas_file_path,
                    "upload_file_name": upload_file_name,
                    "append_file_name": append_file_name
                    
                }
    logger.info(f"rpa connection server request ip: http://{rpa_ip}:{rpa_port}{rpa_url}")
    logger.info(f"rpa connection server request input params: {input_params}")
        
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"http://{rpa_ip}:{rpa_port}{rpa_url}",
                json=input_params,
                timeout=settings.TIMEOUT_SECOND,
            )
    except Exception as ex:
        raise CoreCustomException("C01.006.5001")
    logger.info(f"rpa connection server response status_code : {res.status_code}, response json: {res.json()}")
    
    response_data  = res.json()
    response_status = response_data.get("status", None)
    if str(response_status) == "9999":
        raise CoreCustomException("C01.006.5002")

async def send_rpa_only_cls_FN(session: Session, user_email: str, document_id: str):
    CLS_FN_IDX = 1
    
    select_document_result = query.select_document(session, document_id=document_id)
    select_document_result: schema.DocumentInfo = select_document_result
    
    
    if select_document_result.cls_idx != CLS_FN_IDX: # 해외 투자신고서 이외
        raise CoreCustomException("C01.002.4003")
    
    rpa_template = query.select_rpa_form_info_get_all_latest(session)
    company_user_info = query.select_company_user_info(session, emp_usr_emad=user_email)
    send_email = company_user_info.emp_usr_emad
    
    
    upload_pd_files = []
    append_pd_files = []
    
    # TODO 실제 파일로 변경
    file_path = "/workspace/app/assets/sample/kei2205_rpa_sample_1.xlsx"
    with open(file_path, 'rb') as file:
        df = file.read()
    upload_pd_files.append([os.path.basename(file_path), df])
    append_pd_files.append([os.path.basename(file_path), df])
    
    await send_rpa(
        send_mail_addr = send_email,
        to_mail_addr = rpa_template.rpa_receiver_email,
        cc_mail_addr = "",
        bcc_mail_addr = "",
        subject_title = rpa_template.rpa_title,
        body_data = rpa_template.rpa_body,
        upload_file_list = upload_pd_files, # TODO 실제 파일로 변경
        append_file_list = append_pd_files, # TODO 실제 파일로 변경
        nas_file_path = rpa_template.rpa_nas_path
    )
