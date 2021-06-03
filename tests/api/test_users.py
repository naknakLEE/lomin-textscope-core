from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.const import get_settings
from app.database.schema import Users
from tests.utils.utils import random_email, random_lower_string


settings = get_settings()
fake_info = settings.FAKE_USER_INFORMATION


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token: Dict[str, str]
) -> None:
    response = client.get(f"users/me?token={normal_user_token}")
    current_user = response.json()
    assert current_user["email"] == fake_info["email"]
    assert current_user["full_name"] == fake_info["full_name"]
    assert current_user["username"] == fake_info["username"]

def test_create_user_new_email(
    client: TestClient, superuser_token: dict, get_db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password}
    response = client.post(
        f"/users?token={superuser_token}", json=data,
    )
    assert 200 <= response.status_code < 300
    created_user = response.json()
    user = Users.get(email=email)
    assert user
    assert user.email == created_user["email"]



def test_get_existing_user(
    client: TestClient, superuser_token: dict, get_db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)
    user_email = user.email
    response = client.get(
        f"/users/{user_email}?token={superuser_token}",
    )
    print('\033[96m' + f"test_get_existing_user: {response.json()}" + '\033[0m')
    assert 200 <= response.status_code < 300
    api_user = response.json()
    existing_user = Users.get_by_email(get_db, email=email)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_create_user_existing_username(
    client: TestClient, superuser_token: dict, get_db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)

    data = {"email": email, "password": password}
    response = client.post(
        f"/users?token={superuser_token}", json=data,
    )
    created_user = response.json()
    
    assert response.status_code == 400
    assert "_id" not in created_user


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token: Dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    response = client.post(
        f"/users?token={normal_user_token}", json=data,
    )
    assert response.status_code == 400


def test_retrieve_users(
    client: TestClient, superuser_token: dict, get_db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=username, password=password)

    username2 = random_email()
    password2 = random_lower_string()
    user2 = Users.create(get_db, email=username2, password=password2)

    response = client.get(f"/users?token={superuser_token}")
    all_users = response.json()

    assert len(all_users) > 1
    for item in all_users:
        assert "email" in item
