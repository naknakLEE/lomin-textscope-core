from os import access
import random
import string
from typing import Dict

from fastapi.testclient import TestClient

from app.common.const import get_settings


settings = get_settings()
fake_super_user_info = settings.FAKE_SUPERUSER_INFORMATION


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def get_superuser_token_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "email": fake_super_user_info["email"],
        "password": fake_super_user_info["password"],
    }
    response = client.post("/auth/token", data=login_data)
    tokens = response.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers