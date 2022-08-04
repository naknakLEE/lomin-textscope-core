import pandas as pd
import os
import shutil
from typing import Any, Dict, List, Union
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.utils.logging import logger
from app.common.const import get_settings
from app.schemas import HTTPBearerFake
from app.utils.rpa import send_rpa

settings = get_settings()
router = APIRouter()



@router.post("/drm/decryption")
def drm_decryption(
        params: dict = Body(...)
    ) -> Any:
    try:
        from_file_nm = params.get("from_file_nm")
        to_file_nm = params.get("to_file_nm")
        file_from_path = "/workspace/drm/file_from"
        file_to_path = "/workspace/drm/file_to"
        
        

        isExist = os.path.exists(file_to_path)
        if not isExist:
            os.makedirs(file_to_path)
            
        shutil.copyfile(os.path.join(file_from_path, from_file_nm), os.path.join(file_to_path, to_file_nm))

        
    except Exception as ex:
        res = {
                "msg": "암호화해제중 에러가 발생하였습니다. 관리자에게 문의해주세요.\nERROR Exceptionnull",
                "data": "",
                "status": "9999"
            }
    res = {
        "msg": "암호화해제 정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))


@router.post("/drm/encryption")
def drm_encryption(
        from_file_nm: str,
        to_file_nm: str
    ) -> Any:
    try:
        file_from_path = "/workspace/drm/file_from"
        file_to_path = "/workspace/drm/file_to"
        
        import os
        import shutil

        isExist = os.path.exists(file_to_path)
        if not isExist:
            os.makedirs(file_to_path)
        shutil.copyfile(os.path.join(file_from_path, from_file_nm), os.path.join(file_to_path, to_file_nm))

        
    except Exception as ex:
        res = {
                "msg": "암호화해제중 에러가 발생하였습니다. 관리자에게 문의해주세요.\nERROR Exceptionnull",
                "data": "",
                "status": "9999"
            }
    res = {
        "msg": "암호화해제 정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))





@router.post("/drm/decryption")
def drm_decryption(
        params: dict = Body(...)
    ) -> Any:
    try:
        from_file_nm = params.get("from_file_nm")
        to_file_nm = params.get("to_file_nm")
        file_from_path = "/workspace/drm/file_from"
        file_to_path = "/workspace/drm/file_to"
        
        

        isExist = os.path.exists(file_to_path)
        if not isExist:
            os.makedirs(file_to_path)
            
        shutil.copyfile(os.path.join(file_from_path, from_file_nm), os.path.join(file_to_path, to_file_nm))

        
    except Exception as ex:
        res = {
                "msg": "암호화해제중 에러가 발생하였습니다. 관리자에게 문의해주세요.\nERROR Exceptionnull",
                "data": "",
                "status": "9999"
            }
    res = {
        "msg": "암호화해제 정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))


@router.post("/kei/send_rpa")
async def post_kei_rpa(
        send_mail_addr: str,
        to_mail_addr: str,
        cc_mail_addr: str,
        bcc_mail_addr: str,
        subject_title: str,
        body_data: str,
        upload_file_count: int,
        append_file_count: int
    ) -> Any:
    
    
    
    
    root_path = "/workspace/app/assets/sample/"
    file_list = ["kei2205_rpa_sample_1.xlsx", "kei2205_rpa_sample_2.xlsx"]
    
    upload_pd_files= []
    for i in range((upload_file_count)):
        idx = i % 2 
        file_name = file_list[idx]
        with open(os.path.join(root_path, file_name), 'rb') as file:
            df = file.read()
        upload_pd_files.append([file_name, df])
    
    append_pd_files= []
    for i in range((append_file_count)):
        idx = i % 2 
        file_name = file_list[idx]
        with open(os.path.join(root_path, file_name), 'rb') as file:
            df = file.read()
        append_pd_files.append([file_name, df])
    
    await send_rpa(
        send_mail_addr,
        to_mail_addr,
        cc_mail_addr,
        bcc_mail_addr,
        subject_title,
        body_data,
        upload_pd_files,
        append_pd_files
    )
    res = {
        "msg": "정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }
    return JSONResponse(content=jsonable_encoder(res))





@router.post("/rpa/sendDwpMail")
def drm_decryption(
        params: dict = Body(...)
    ) -> Any:
    try:
        send_mail_addr = params.get("send_mail_addr")
        to_mail_addr = params.get("to_mail_addr")
        cc_mail_addr = params.get("cc_mail_addr")
        bcc_mail_addr = params.get("bcc_mail_addr")
        subject_title = params.get("subject_title")
        body_data = params.get("body_data")
        upload_file_name = params.get("upload_file_name")
        append_file_name = params.get("append_file_name")
        
        
        logger.info(f"/test/rpa/sendDwpMail inputs \n\
            send_mail_addr: {send_mail_addr} \n\
            to_mail_addr: {to_mail_addr} \n\
            cc_mail_addr: {cc_mail_addr} \n\
            bcc_mail_addr: {bcc_mail_addr} \n\
            subject_title: {subject_title} \n\
            body_data: {body_data} \n\
            upload_file_name: {upload_file_name} \n\
            append_file_name: {append_file_name} \n\
            ")
        
        
        nas_path = "/workspace/data/file_attach"
        separator = "||"
        
        upload_files = upload_file_name.split(separator)[:-1]
        append_files = append_file_name.split(separator)[:-1]
        
        for file_name in upload_files:
            file_path = os.path.join(nas_path, file_name)
            with open(os.path.join(file_path, file_name), 'rb') as file:
                read_test = file.read()
                
        for file_name in append_files:
            file_path = os.path.join(nas_path, file_name)
            with open(os.path.join(file_path, file_name), 'rb') as file:
                read_test = file.read()

        
    except Exception as ex:
        res = {
            "msg": "에러가 발생하였습니다. 관리자에게 문의해주세요.",
            "data": "",
            "errMsg": "javax.mail.MessagingException: IOException while sending message;\n  nested exception is:\n\tjava.io.FileNotFoundException: /data/file_attach/202207221234567890.xlsx (No such file or directory)",
            "status": "9999"
        }
    res = {
        "msg": "정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))
