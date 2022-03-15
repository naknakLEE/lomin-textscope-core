from ldap3 import Connection, Server
from typing import Dict
from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# from fastapi.security import OAuth2PasswordRequestForm

from app.errors import exceptions as ex
from app.models import Token, LoginForm
from app.schemas.json_schema import auth_token_responses
from app.utils.auth import create_access_token, initialize_ldap
from app.common.const import get_settings
from app.database.connection import db
from app.utils.utils import print_error_log


settings = get_settings()
router = APIRouter()


@router.post("/token", response_model=Token, responses=auth_token_responses)
async def login_for_access_token(
    form_data: LoginForm = Depends(),
    session: Session = Depends(db.session),
    ldap_server: Server = Depends(initialize_ldap),
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
    user = "cn={},ou=users,dc=lomin,dc=ai".format(form_data.cn)
    try:
        with Connection(ldap_server, user=user, password=form_data.password) as conn:
            conn.search(
                "dc=lomin,dc=ai", "(cn={})".format(form_data.cn), attributes=["mail"]
            )
            mail = conn.entries[0].mail.value
    except Exception:
        print_error_log()
        raise ex.NotFoundUserException(email=form_data.cn)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": mail},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# @router.post("/login/test", status_code=200)
# async def login(user_info: models.UserRegister):
#     is_exist = is_email_exist(user_info.email)
#     if not user_info.email or not user_info.password:
#         return JSO
# NResponse(status_code=400, content=dict(msg="Email and PW must be provided'"))
#     if not is_exist:
#         return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
#     user = Users.get(session, email=user_info.email)
#     is_verified = verify_password(user_info.password, user.hashed_password)
#     if not is_verified:
#         return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER OR PW?"))
#     token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}),)}")
#     return token
