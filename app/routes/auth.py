from datetime import timedelta

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from models import Token
from utils.authorization import (
    authenticate_user,
    create_access_token,
)
from common.const import get_settings


settings = get_settings()
router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(settings.FAKE_INFORMATION, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# @router.post("/login/test", status_code=200)
# async def login(user_info: models.UserRegister):
#     is_exist = is_email_exist(user_info.email)
#     if not user_info.email or not user_info.password:
#         return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided'"))
#     if not is_exist:
#         return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
#     user = Users.get(email=user_info.email)
#     is_verified = verify_password(user_info.password, user.hashed_password)
#     if not is_verified:
#         return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER OR PW?"))
#     token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}),)}")
#     return token
