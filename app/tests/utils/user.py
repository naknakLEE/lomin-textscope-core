from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.models import User, UserUpdate
from app.database.schema import Users
from app.tests.utils.utils import random_email, random_lower_string
from app.utils.auth import get_password_hash


settings = get_settings()


def user_authentication(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"email": email, "password": password}

    r = client.post("/auth/token", data=data)
    response = r.json()
    print('\033[96m' + f"user_authentication: {response}" + '\033[0m')
    auth_token = response["access_token"]
    return auth_token


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user = Users.create(username=email, email=email, password=password)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> Dict[str, str]:
    password = random_lower_string()
    user = Users.get(email = email)
    del user.id, user.updated_at, user.created_at, user._sa_instance_state
    current_user = {}
    for key in user.__dict__: 
        current_user[key] = getattr(user, key)
    user = UserUpdate(**current_user)
    if not user:
        user = Users.create(db, username=email, email=email, password=password)
    else:
        hashed_password = get_password_hash(password)
        user_in_update = UserUpdate(hashed_password=hashed_password)
        user_in_update.hashed_password = hashed_password
        user = Users.update(db, db_obj=user, obj_in=user_in_update)
        
    return user_authentication(client=client, email=email, password=password)