import traceback
import pandas as pd
import os
import base64
import shutil
from typing import Any, Dict, List, Union
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import APIRouter, File, UploadFile, Body

from app.config import hydra_cfg
from app.utils.logging import logger
from app.common.const import get_settings
from app.schemas import HTTPBearerFake
from app.utils.rpa import send_rpa
from app.utils.drm import load_file2base64, DRM


settings = get_settings()
router = APIRouter()


@router.post("/java/drm/decryption")
def post_java_drm_decryption(
        params: dict = Body(...)
    ) -> Any:
    try:
        from_file_nm = params.get("from_file_nm")
        to_file_nm = params.get("to_file_nm")
        drm_user = params.get("drm_user")
        
        logger.info(f"/java/drm/decryption inputs: \n\
            from_file_nm: {from_file_nm}  \n\
            to_file_nm: {to_file_nm}  \n\
            drm_user: {drm_user}  \n\
                ")
        drm_cfg = hydra_cfg.common.drm
        file_from_path = drm_cfg.save_path
        file_to_path = drm_cfg.get_path
        

        isExist = os.path.exists(file_to_path)
        if not isExist:
            os.makedirs(file_to_path)
            
        shutil.copyfile(os.path.join(file_from_path, from_file_nm), os.path.join(file_to_path, to_file_nm))

        
    except Exception as ex:
        traceback.print_exc()
        res = {
                "msg": "암호화해제중 에러가 발생하였습니다. 관리자에게 문의해주세요.\nERROR Exceptionnull",
                "data": "",
                "status": "9999"
            }
        return JSONResponse(content=jsonable_encoder(res))
    res = {
        "msg": "암호화해제 정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))


@router.post("/java/drm/encryption")
def post_java_drm_encryption(
        params: dict = Body(...)
    ) -> Any:
    try:
        from_file_nm = params.get("from_file_nm")
        to_file_nm = params.get("to_file_nm")
        drm_user = params.get("drm_user")
        drm_cfg = hydra_cfg.common.drm
        file_from_path = drm_cfg.save_path
        file_to_path = drm_cfg.get_path
        
        logger.info(f"/java/drm/decryption inputs: \n\
            from_file_nm: {from_file_nm}  \n\
            to_file_nm: {to_file_nm}  \n\
            drm_user: {drm_user}  \n\
                ")

        isExist = os.path.exists(file_to_path)
        if not isExist:
            os.makedirs(file_to_path)
        shutil.copyfile(os.path.join(file_from_path, from_file_nm), os.path.join(file_to_path, to_file_nm))

        
    except Exception as ex:
        traceback.print_exc()
        res = {
                "msg": "암호화해제중 에러가 발생하였습니다. 관리자에게 문의해주세요.\nERROR Exceptionnull",
                "data": "",
                "status": "9999"
            }
        return JSONResponse(content=jsonable_encoder(res))
    res = {
        "msg": "암호화해제 정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))


@router.post("/java/rpa/sendDwpMail")
async def post_java_rpa_sendDwpMail(
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
        dwp_file_path = params.get("dwp_file_path")
        
        
        logger.info(f"/test/rpa/sendDwpMail inputs \n\
            send_mail_addr: {send_mail_addr} \n\
            to_mail_addr: {to_mail_addr} \n\
            cc_mail_addr: {cc_mail_addr} \n\
            bcc_mail_addr: {bcc_mail_addr} \n\
            subject_title: {subject_title} \n\
            body_data: {body_data} \n\
            upload_file_name: {upload_file_name} \n\
            append_file_name: {append_file_name} \n\
            dwp_file_path: {dwp_file_path} \n\
            ")
        
        rpa_cfg = hydra_cfg.common.rpa
        nas_path = dwp_file_path
        separator = rpa_cfg.file_name_separator
        
        logger.info(f"upload_file_name {upload_file_name}")
        logger.info(f"append_file_name {append_file_name}")
        upload_files = upload_file_name.split(separator)
        append_files = append_file_name.split(separator)
        
        for file_name in upload_files:
            file_path = os.path.join(nas_path, file_name)
            with open(file_path, 'rb') as file:
                read_test = file.read()
                
        for file_name in append_files:
            file_path = os.path.join(nas_path, file_name)
            with open(file_path, 'rb') as file:
                read_test = file.read()

        
    except Exception as ex:
        traceback.print_exc()
        res = {
            "msg": "에러가 발생하였습니다. 관리자에게 문의해주세요.",
            "data": "",
            "errMsg": "javax.mail.MessagingException: IOException while sending message;\n  nested exception is:\n\tjava.io.FileNotFoundException: /data/file_attach/202207221234567890.xlsx (No such file or directory)",
            "status": "9999"
        }
        return JSONResponse(content=jsonable_encoder(res))
    res = {
        "msg": "정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }

    return JSONResponse(content=jsonable_encoder(res))



@router.post("/kei/send_rpa")
async def post_kei_send_rpa(
        send_mail_addr: str,
        to_mail_addr: str,
        cc_mail_addr: str,
        bcc_mail_addr: str,
        subject_title: str,
        body_data: str,
        dwp_file_path: str,
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
    
    logger.info(f"call send_rpa upload_pd_files len: {len(upload_pd_files)} append_pd_files len: {len(append_pd_files)}")
    await send_rpa(
        send_mail_addr,
        to_mail_addr,
        cc_mail_addr,
        bcc_mail_addr,
        subject_title,
        body_data,
        dwp_file_path,
        upload_pd_files,
        append_pd_files
    )
    res = {
        "msg": "정상처리 되었습니다.",
        "data": "",
        "status": "0000"
    }
    return JSONResponse(content=jsonable_encoder(res))




@router.post("/kei/encryption")
async def post_kei_encryption(\
        user_email: str,
        file: UploadFile = File(..., description= "암호화 할 문서"),
        
    ) -> Any:
    
    document_name = file.filename
    document_data = await file.read()
    encoded_image_data = base64.b64encode(document_data)
    drm = DRM()
    document_data = await drm.drm_encryption(encoded_image_data, document_name, user_email)
    
    return {"msg": "sucess"}


@router.post("/kei/decryption")
async def post_kei_decryption(
        user_email: str,
        file: UploadFile = File(..., description= "복호화 할 문서"),
    ) -> Any:
    
    document_name = file.filename
    document_data = await file.read()
    encoded_image_data = base64.b64encode(document_data)
    drm = DRM()
    document_data = await drm.drm_decryption(encoded_image_data, document_name, user_email)
    
    return {"msg": "sucess"}



