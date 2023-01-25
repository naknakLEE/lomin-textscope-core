from typing import Dict
from datetime import timedelta
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from jose import jwt


from app.config import hydra_cfg
from app.models import Token, OAuth2PasswordRequestForm
from app.schemas.json_schema import auth_token_responses
from app.common.const import get_settings
from app.database import query
from app.utils.logging import logger
from app.database.connection import db
from app.models import UserInfo as UserInfoInModel
from app.service.auth import (
    login_for_access_token as login_for_access_token_service,
    token_validation as token_validation_service
)
from app.middlewares.exception_handler import CoreCustomException
from app.utils.auth import create_access_token

from app.utils.auth import get_current_active_user as get_current_active_user_token_validation
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


settings = get_settings()
router = APIRouter()

@router.post("/kei/sso/token", response_model=Token, responses=auth_token_responses)
async def post_kei_sso_token(
    request: Request,
    params: dict = Body(...),
    session: Session = Depends(db.session),
) -> Dict:
    
    secret_key = "ZCZnhNcW0D9P7EgbYzkc9/KI1H2syha1zHQ7LDeFY/YU9pCSWyqi6ctKatHZ0hDs"
    algorithms ="HS256"
    
    token = params.get("token")
    
    try:
        token_info = jwt.decode(token, secret_key, algorithms=[algorithms])
    except:
        raise CoreCustomException("C01.004.5001")
    
    compNm = token_info.get("compNm", None)
    sub = token_info.get("sub", None)
    uid = token_info.get("UID")
    exp = token_info.get("exp", None)

    logger.info(f"jwt decode info compNm: {compNm} sub: {sub} uid: {uid} exp: {exp}")
    
    user = query.select_vw_if_emp(session, eno = uid)
    if user is None:
        raise CoreCustomException(2401)
    
    user_email = user.usr_emad
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user_email,
            "scopes": [],
            "loc": request.state.ip
        },
        expires_delta=access_token_expires,
    )
    
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder({
            "access_token": access_token,
            "token_type": "bearer",
            "email": user_email
        })
    )


@router.post("/token", response_model=Token, responses=auth_token_responses)
async def login_for_access_token(
    request: Request,
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
    return await login_for_access_token_service(
        form_data = form_data,
        session = session
    )


@router.get("/token/validation")
async def token_validation(
    current_user: UserInfoInModel = Depends(get_current_active_user_token_validation),
    session: Session = Depends(db.session)
) -> JSONResponse:
    
    return await token_validation_service(
        current_user = current_user,
        session = session
    )