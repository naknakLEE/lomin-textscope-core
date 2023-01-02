from copy import copy, deepcopy
import uuid
from app.utils.image import get_image_bytes

from httpx import Client

from typing import Any, Dict, Tuple, TypeVar
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import hydra_cfg
from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.utils import get_pp_api_name, set_json_response, get_ts_uuid
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app.schemas.json_schema import inference_responses
from app.models import UserInfo as UserInfoInModel
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict
from app.utils.logging import logger
from app.utils.inference import get_removed_text_inference_result
from app.wrapper import pp, pipeline, settings
from app.database import query, schema
from app.database.connection import db
from app.schemas import error_models as ErrorResponse
from app.errors import exceptions as ex


from app.service.inference import (
    ocr as ocr_service,
    ocr_old as ocr_old_service
)
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()

Pipeline = TypeVar("Pipeline")
PIPELINE_GOCR = pipeline.gocr_
PIPELINE_CLS = pipeline.cls_
PIPELINE_KV = pipeline.kv_
PIPELINE_IDCARD = pipeline.idcard_

INFERENCE_PIPELINE: Dict[str, Tuple[str, Pipeline]] = {
    "gocr":   [ ("gocr", PIPELINE_GOCR), ],
    "cls":    [ ("gocr", PIPELINE_GOCR), ("cls", PIPELINE_CLS) ],
    "kv":     [ ("gocr", PIPELINE_GOCR),                        ("kv", PIPELINE_KV) ],
    "cls-kv": [ ("gocr", PIPELINE_GOCR), ("cls", PIPELINE_CLS), ("kv", PIPELINE_KV) ],
    
    "idcard": [ ("idcard", PIPELINE_IDCARD) ]
}


@router.post("/ocr", status_code=200, responses=inference_responses)
def ocr(
    *,
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    return ocr_service(
        request = request,
        inputs = inputs,
        current_user = current_user,
        session = session
    )

# TODO: 토큰을 이용한 유저 체크 부분 활성화
@router.post("/ocr/old", status_code=200, responses=inference_responses)
def ocr_old(
    *,
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    cls-kv 적용전 ocr

    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    return ocr_old_service(
        request = request,
        inputs = inputs,
        current_user = current_user,
        session = session
    )
