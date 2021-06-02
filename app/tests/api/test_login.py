from typing import Dict

from fastapi.testclient import TestClient

from app.common.const import get_settings


settings = get_settings()
fake_super_user_info = settings.FAKE_INFORMATION

def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "email": fake_super_user_info["email"],
        "password": fake_super_user_info["password"]
    }
    response = client.post(f"/auth/token", data=login_data)
    tokens = response.json()
    assert response.status_code == 200
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"


def test_use_access_token(
    client: TestClient, superuser_token: Dict[str, str]
) -> None:
    response = client.get(f"/users/me?token={superuser_token}")
    result = response.json()
    assert response.status_code == 200
    assert "username" in result
    assert "email" in result
    assert "full_name" in result
