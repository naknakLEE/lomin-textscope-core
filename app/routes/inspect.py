import copy
from datetime import datetime
from typing import List
from app.services.inspect import get_diff_array_item_indexes, get_inspect_accuracy, get_item_list_in_index, get_flatten_table_content, get_removed_changes_keyvalue

from fastapi import APIRouter, Depends, Body, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import db
from app.database import query, schema
from app.common.const import settings
from app.utils.logging import logger
from app.utils.utils import get_ts_uuid, is_admin
from app.schemas import error_models as ErrorResponse
from app.models import UserInfo as UserInfoInModel
from app.service.inspect import (
    kbl_post_inspect_info as kbl_post_inspect_info_service,
    post_inspect_info as post_inspect_info_service
)
if settings.BSN_CONFIG.get("USE_TOKEN", False):
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


@router.post("/save")
def kbl_post_inspect_info(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    '''
    교보생명 고객사 검수 데이터 저장
    교보생명은 개인정보 이슈로 inference 데이터를 직접 저장할 수 없습니다. 그래서 매번 inference 결과를 받아서 inspect와 비교하고,
    거기서 달라진 것을 기반으로 정확도를 산출합니다. 그리고 최종 검수 결과는 kv의 경우 항목코드만 남기고 tables의 경우 인덱스만 남깁니다.
    '''
    return kbl_post_inspect_info_service(
        request = request, 
        params = params, 
        current_user = current_user, 
        session = session
        )


@router.post("/save/old")
def post_inspect_info(
    request: Request,
    params: dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    """
    검수 정보 임시 저장 및 저장
    TODO 에러응답 추가
        inspect_date_startㅣ 없을때
        inspect_done True인데 inpsect_end_time이 없을때
    """
    return post_inspect_info_service(
        request = request, 
        params = params, 
        current_user = current_user, 
        session = session
        )
