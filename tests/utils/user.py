from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.models import UserInDB
from app.database.schema import Users
from tests.utils.utils import random_lower_string


settings = get_settings()


def user_authentication(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"email": email, "password": password}

    r = client.post("/auth/token", data=data)
    response = r.json()
    # print("\033[96m" + f"user_authentication: {response}" + "\033[0m")
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def authentication_token_from_email(
    *, client: TestClient, email: str, get_db: Session
) -> Dict[str, str]:
    password = random_lower_string()
    data = {"email": email}
    user = Users.get(get_db, kwargs=data)
    if user:
        del user.id, user.updated_at, user.created_at, user._sa_instance_state
        user_in = UserInDB(**user.__dict__, password=password)
        if not user:
            data = {"email": email, "password": password, "username": user.username}
            user = Users.create(get_db, kwargs=data)
        else:
            user = Users.update(get_db, kwargs=user_in.dict())
            user = Users.get(email=email)

        return user_authentication(client=client, email=email, password=password)
    return {"Authorization": "None"}
