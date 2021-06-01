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


router = APIRouter()

FAKE_INFORMATION2: dict = {
        "username": "hai",
        "full_name": "hai",
        "email": "hai@example.com",
        "password": "123456",
        "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    }

@router.get("/")
def read_users(
    session: Session = Depends(db.session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    users = Users.get_multi(session, skip=skip, limit=limit)
    return users


@router.post("/")
def create_user(
    *,
    session: Session = Depends(db.session),
    user: Dict,
    current_user: User = Depends(get_current_active_user)
):
    is_exist = Users.get_by_email(db, email=user["email"])
    if is_exist:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = Users.create(session, auto_commit=True, **user)
    return user


@router.put("/me", response_model=User)
def update_user_me(
    *,
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
    user = Users.update(session, db_obj=current_user, obj_in=user_in)


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/me/items")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "SY_item", "owner": current_user.username}]
