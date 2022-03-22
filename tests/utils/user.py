from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.database.schema import Users
from tests.utils.utils import random_lower_string


settings = get_settings()


def user_authentication(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"email": email, "password": password}
    result = client.post("v1/auth/token", data=data).json()
    auth_token = result["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def authentication_token_from_email(
    *, client: TestClient, email: str, get_db: Session
) -> Dict[str, str]:
    password = random_lower_string()
    data = {"email": email}
    user = Users.get(get_db, **data)
    if user:
        user = Users.update(get_db, id=user.id, password=password)
        user = Users.get(get_db, email=email)
    elif not user:
        data = {"email": email, "password": password}
        user = Users.create(get_db, **data)
    return user_authentication(client=client, email=email, password=password)


def get_normaluser_token_headers(client: TestClient) -> Dict[str, str]:
    fake_guestuser_info = settings.FAKE_GUESTUSER_INFORMATION
    login_data = {
        "email": fake_guestuser_info["email"],
        "password": fake_guestuser_info["password"],
    }
    response = client.post("v1/auth/token", data=login_data)
    tokens = response.json()
    print("\033[95m" + f"tokens: {tokens}" + "\033[m")
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


def get_superuser_token_headers(client: TestClient) -> Dict[str, str]:
    fake_super_user_info = settings.FAKE_SUPERUSER_INFORMATION
    login_data = {
        "email": fake_super_user_info["email"],
        "password": fake_super_user_info["password"],
    }
    response = client.post("v1/auth/token", data=login_data)
    tokens = response.json()
    print("\033[95m" + f"tokens: {tokens}" + "\033[m")
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers