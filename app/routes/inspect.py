from fastapi import APIRouter, Depends, Body, Request, Security
from fastapi.encoders import jsonable_encoder
from fastapi import BackgroundTasks
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import hydra_cfg
from app.database.connection import db
from app.common.const import get_settings
from app.models import UserInfo as UserInfoInModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.service.inspect import (
    kbl_post_inspect_info as kbl_post_inspect_info_service,
    post_inspect_info as post_inspect_info_service
)
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


security = HTTPBearer()
settings = get_settings()
router = APIRouter()


# @router.post("/save")
# def kbl_post_inspect_info(
#     request: Request,
#     params: dict = Body(...),
#     current_user: UserInfoInModel = Depends(get_current_active_user),
#     session: Session = Depends(db.session)
# ) -> JSONResponse:
#     '''
#     교보생명 고객사 검수 데이터 저장

#     교보생명은 개인정보 이슈로 inference 데이터를 직접 저장할 수 없습니다. 그래서 매번 inference 결과를 받아서 inspect와 비교하고,
#     거기서 달라진 것을 기반으로 정확도를 산출합니다. 그리고 최종 검수 결과는 kv의 경우 항목코드만 남기고 tables의 경우 인덱스만 남깁니다.


#     '''
#     return kbl_post_inspect_info_service(
#         request = request, 
#         params = params, 
#         current_user = current_user, 
#         session = session
#         )





# @router.post("/save/old")
# def post_inspect_info(
#     request: Request,
#     params: dict = Body(...),
#     current_user: UserInfoInModel = Depends(get_current_active_user),
#     session: Session = Depends(db.session)
# ) -> JSONResponse:
#     """
#     검수 정보 임시 저장 및 저장
#     TODO 에러응답 추가
#         inspect_date_startㅣ 없을때
#         inspect_done True인데 inpsect_end_time이 없을때
#     """
#     return post_inspect_info_service(
#         request = request, 
#         params = params, 
#         current_user = current_user, 
#         session = session
#         )


@router.post("/save")
async def post_inspect_info(
    request: Request,
    params: dict = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: HTTPAuthorizationCredentials = Security(security),
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
        background_tasks = background_tasks,
        current_user = current_user,
        session = session
    )

