from typing import Any, Dict, List

from fastapi import Depends, APIRouter, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr

from app.utils.auth import (
    get_current_active_user
)
from app.models import User
from app.database.connection import db
from app.database.schema import Users, UserUpdate
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex 


router = APIRouter()


@router.get("")
def read_users(
    session: Session = Depends(db.session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    users = Users.get_multi(session, skip=skip, limit=limit)
    return users


@router.post("", response_model=User)
def create_user(
    session: Session = Depends(db.session),
    user: Dict = {},
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    is_exist = Users.get(session, email=user["email"])
    if is_exist:
        raise ex.AlreadyExistException(current_user.email)
    user["hashed_password"] = get_password_hash(user["password"])
    created_user = Users.create(session, auto_commit=True, **user)
    return created_user


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    session: Session = Depends(db.session),
    email: EmailStr = None,
    full_name: str = None,
    username: str = None,
    password: str = None,
    current_user: User = Depends(get_current_active_user)
):
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if password is not None:
        user_in.hashed_password = get_password_hash(password)
    if full_name is not None:
        user_in.full_name = full_name
    if username is not None:
        user_in.username = username
    if email is not None:
        user_in.email = email
    updated_user = Users.update(session, db_obj=current_user, obj_in=user_in)
    user = User(**updated_user)
    return user


@router.get("/{user_email}")
def read_user_by_email(
    user_email: EmailStr,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
):
    user = Users.get(session, email=user_email)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    return user


@router.put("/{user_email}")
def update_user(
    *,
    session: Session = Depends(db.session),
    user_email: EmailStr,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    user = Users.get(session, email=user_email)
    if not current_user.is_superuser:
        raise ex.PrivielgeException(current_user.email)
    if not user:
        raise ex.AlreadyExistException(current_user.email)
    user = Users.update(session, db_obj=user, obj_in=user_in)
    return user
