from typing import Dict

from fastapi.testclient import TestClient

from app.common.const import get_settings


settings = get_settings()
fake_super_user_info = settings.FAKE_SUPERUSER_INFORMATION


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "email": fake_super_user_info["email"],
        "password": fake_super_user_info["password"],
    }
    response = client.post("v1/auth/token", data=login_data)
    tokens = response.json()
    assert response.status_code == 200
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"


def test_use_access_token(
    client: TestClient, superuser_token_headers: Dict[str, str]
) -> None:
    response = client.get("v1/users/me", headers=superuser_token_headers)
    result = response.json()
    # print("\033[96m" + f"response: {result}, {superuser_token_headers}" + "\033[m")
    assert response.status_code == 200
    assert "username" in result
    assert "email" in result
    assert "full_name" in result
