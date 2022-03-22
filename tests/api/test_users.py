from typing import Dict

from fastapi.testclient import TestClient
from app.common.const import get_settings
from tests.utils.utils import random_email, random_lower_string


settings = get_settings()


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: Dict[str, str]
) -> None:
    response = client.get(f"v1/users/me", headers=normal_user_token_headers)
    print('\033[096m' + f"email: {response.text}" + '\033[m')
    current_user = response.json()
    fake_guestuser_info = settings.FAKE_GUESTUSER_INFORMATION
    assert current_user["email"] == fake_guestuser_info["email"]
    assert current_user["full_name"] == fake_guestuser_info["full_name"]
    assert current_user["username"] == fake_guestuser_info["username"]


def test_create_user_new_email(
    client: TestClient, superuser_token_headers: dict
) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password}
    response = client.post(
        f"v1/admin/users/create", json=data, headers=superuser_token_headers
    )
    assert 200 <= response.status_code < 300
    created_user = response.json()
    user = client.get(
            "v1/admin/users/{}".format(created_user.get("email")), headers=superuser_token_headers
        ).json()
    assert user
    assert user.get("email") == created_user.get("email")


def test_get_existing_user(
    client: TestClient, superuser_token_headers: dict
) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password}
    user = client.post(
        "v1/admin/users/create", json=data, headers=superuser_token_headers
    ).json()
    existing_user = client.get(
        "v1/admin/users/{}".format(user.get("email")), headers=superuser_token_headers
    ).json()
    assert existing_user["email"] == user["email"]


def test_create_user_existing_username(
    client: TestClient, superuser_token_headers: dict
) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password}
    created_user = client.post(
        "v1/admin/users/create", json=data, headers=superuser_token_headers
    ).json()
    response = client.post(
        "v1/admin/users/create", json=data, headers=superuser_token_headers
    )
    assert response.status_code == 400
    assert "_id" not in created_user


def test_retrieve_users(
    client: TestClient, superuser_token_headers: dict
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    client.post(
        "v1/admin/users/create", json=data, headers=superuser_token_headers
    )

    username2 = random_email()
    password2 = random_lower_string()
    data2 = {"email": username2, "password2": password2}
    client.post(
        "v1/admin/users/create", json=data2, headers=superuser_token_headers
    )

    response = client.get(f"v1/admin/users", headers=superuser_token_headers)
    all_users = response.json()

    assert len(all_users) > 0
    for item in all_users:
        assert "email" in item
