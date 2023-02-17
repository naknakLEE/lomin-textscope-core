from typing import Dict

from app.database.connection import db
from typing import Dict
from fastapi import APIRouter, Body, Depends, Request

from sqlalchemy.orm import Session

from app.schemas.json_schema import inference_responses
from app.models import UserInfo as UserInfoInModel
from app.wrapper import settings
from app.database.connection import db
from app.service.inference import (
    ocr as ocr_service,
    ocr_old as ocr_old_service
)
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()

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
