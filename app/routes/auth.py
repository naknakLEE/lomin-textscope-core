from typing import Dict
from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app import hydra_cfg
from app.models import Token, OAuth2PasswordRequestForm
from app.schemas.json_schema import auth_token_responses
from app.utils.auth import create_access_token, authenticate_user
from app.utils.utils import is_admin
from app.common.const import get_settings
from app.database import query
from app.database.connection import db
from app.models import UserInfo as UserInfoInModel
from app.schemas import error_models as ErrorResponse
from app.middlewares.exception_handler import CoreCustomException

if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


settings = get_settings()
router = APIRouter()


@router.post("/token", response_model=Token, responses=auth_token_responses)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(db.session),
) -> Dict:
    """
    ### email과 password를 받아 OAuth2 호환 토큰 발급
    입력 데이터: 이메일, 비밀번호 <br/>
    출력 데이터: 토큰, 토큰 타입 <br/><br/>
    ***
    토큰은 email, scopes, expires 정보 포함
    -  email: 해당 유저 이메일
    -  scopes: 해당 토큰의 사용 가능한 범위 조정
    -  expires: token 만료 시간 설정

    """
    user = authenticate_user(form_data.email, form_data.password, session)
    if user is None:
        raise CoreCustomException(2401)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.email, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    
    
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder({
            "access_token": access_token,
            "token_type": "bearer"
        })
    )


@router.get("/token/validation")
async def token_validation(
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session)
) -> JSONResponse:
    
    if isinstance(current_user, JSONResponse):
        return current_user
    
    admin = False
    # 사용자의 모든 정책(권한) 확인
    user_policy_result = query.get_user_group_policy(session, user_email=current_user.email)
    if isinstance(user_policy_result, JSONResponse):
        admin = False
    else:
        admin = is_admin(user_policy_result)
    
    
    response = dict(
        email=current_user.email,
        user_team=current_user.team,
        name=current_user.name,
        admin=str(admin)
    )
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response))
