from typing import Dict
from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.errors import exceptions as ex
from app.models import Token, OAuth2PasswordRequestForm
from app.schemas.json_schema import auth_token_responses
from app.utils.auth import create_access_token, authenticate_user
from app.common.const import get_settings
from app.database.connection import db


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
    if not user:
        raise ex.NotFoundUserException(email=form_data.email)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.email, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
