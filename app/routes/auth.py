import os

from datetime import  timedelta

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from database.schema import Users
from models import Token, UserToken
from utils.authorization import (
    authenticate_user, 
    create_access_token, 
    verify_password,
    is_email_exist
)

import models




router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

fake_information = {
    "shinuk": {
        "username": "shinuk",
        "full_name": "Shinuk Yi",
        "email": "shinuk@example.com",
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_information, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/test", status_code=200)
async def login(user_info: models.UserRegister):
    is_exist = is_email_exist(user_info.email)
    if not user_info.email or not user_info.password:
        return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided'"))
    if not is_exist:
        return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
    user = Users.get(email=user_info.email)
    
    is_verified = verify_password(user_info.password, user.hashed_password)
    if not is_verified:
        return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER OR PW?"))
    token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}),)}")
    return token