from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.models import User, UserUpdate, UserInDB
from app.database.schema import Users
from tests.utils.utils import random_email, random_lower_string
from app.utils.auth import get_password_hash


settings = get_settings()


def user_authentication(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"email": email, "password": password}

    r = client.post("/auth/token", data=data)
    response = r.json()
    print("\033[96m" + f"user_authentication: {response}" + "\033[0m")
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(get_db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, get_db: Session
) -> Dict[str, str]:
    password = random_lower_string()
    user = Users.get(email=email)
    print("\033[96m" + f"password1: {user.__dict__}" + "\033[0m")
    del user.id, user.updated_at, user.created_at, user._sa_instance_state
    # current_user = {}
    # for key in user.__dict__:
    #     current_user[key] = getattr(user, key)
    user_in = UserInDB(**user.__dict__, password=password)
    if not user:
        user = Users.create(
            get_db, username=user.username, email=email, password=password
        )
    else:
        print("\033[96m" + f"password2: {user_in.__dict__}" + "\033[0m")
        # hashed_password = get_password_hash(password)
        # current_user["hashed_password"] = hashed_password
        # user_in_update = UserInDB(**current_user)
        user = Users.update(get_db, db_obj=user, obj_in=user_in)
        user = Users.get(email=email)
        print("\033[96m" + f"password3: {user.__dict__}" + "\033[0m")

    return user_authentication(client=client, email=email, password=password)
