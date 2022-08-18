import os

import traceback
import httpx
import base64
import pandas as pd
import urllib.parse
from typing import Optional, List, Any
from httpx import AsyncClient
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.database import query, schema
from app import hydra_cfg
from app.common.const import get_settings
from app.utils.logging import logger
from app.middlewares.exception_handler import CoreCustomException


settings = get_settings()
textscope_plugin_dashboard = f"http://{settings.PLUGIN_DASHBOARD_IP_ADDR}:{settings.PLUGIN_DASHBOARD_IP_PORT}"



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
                    "dwp_file_path": nas_file_path,
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
    
async def request_get_kv_excel(document_id: str, token: HTTPAuthorizationCredentials):
    
    params= dict(
        document_id=document_id,
    )
    
    headers = dict()
    if isinstance(token, HTTPAuthorizationCredentials):
        headers["Authorization"] = " ".join([token.scheme, token.credentials])
    
    async with AsyncClient() as client:
        response = await client.get(
            f'{textscope_plugin_dashboard}/download/documents/excel',
            params=params,
            timeout=settings.TIMEOUT_SECOND,
            headers=headers
        )
    
    # response_metadata = set_response_metadata(request_datetime)
    logger.info(f"download/documents/excel response status: {response.status_code}")
    status_code = response.status_code
    if status_code != 200:
        response_data = response.json()
        logger.warning(f"download/documents/excel error {response_data}")
        raise CoreCustomException("C01.006.5003")
        
        
    else:
        excel_file_name = urllib.parse.quote(params.get("document_filename", document_id))
        headers = {'Content-Disposition': f'attachment; filename="{excel_file_name}.xlsx"'}
        
    excel_file_name = f"{excel_file_name}.xlsx"
    logger.info(f"download/documents/excel sucess {excel_file_name}")
    
    return response.content, excel_file_name

async def send_rpa_only_cls_FN(session: Session, user_email: str, document_id: str, token: HTTPAuthorizationCredentials):
    CLS_FN_IDX = 1
    
    select_document_result = query.select_document(session, document_id=document_id)
    if isinstance(select_document_result, JSONResponse):
        raise CoreCustomException(2101)
    select_document_result: schema.DocumentInfo = select_document_result
    
    
    if select_document_result.cls_idx != CLS_FN_IDX: # 해외 투자신고서 이외
        raise CoreCustomException("C01.002.4003")
    
    kv_excel_bytes, kv_excel_filename = await request_get_kv_excel(document_id, token)
    rpa_template = query.select_rpa_form_info_get_all_latest(session)
    company_user_info = query.select_company_user_info(session, emp_usr_emad=user_email)
    send_email = company_user_info.emp_usr_emad
    
    
    upload_pd_files = []
    append_pd_files = []
    
    upload_pd_files.append([kv_excel_filename, kv_excel_bytes])
    append_pd_files.append([kv_excel_filename, kv_excel_bytes])
    
    await send_rpa(
        send_mail_addr = send_email,
        to_mail_addr = rpa_template.rpa_receiver_email,
        cc_mail_addr = "",
        bcc_mail_addr = "",
        subject_title = rpa_template.rpa_title,
        body_data = rpa_template.rpa_body,
        upload_file_list = upload_pd_files,
        append_file_list = append_pd_files,
        nas_file_path = rpa_template.rpa_nas_path
    )
