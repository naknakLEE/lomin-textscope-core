import os
import os
import shutil
from typing import Any, Dict, List, Union
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.common.const import get_settings
from app.schemas import HTTPBearerFake

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

