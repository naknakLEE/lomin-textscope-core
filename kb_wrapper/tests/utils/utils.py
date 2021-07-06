import random
import string

from sqlalchemy.orm import Session
from typing import Dict, Optional
from fastapi.testclient import TestClient

from kb_wrapper.app.common.const import get_settings


settings = get_settings()
fake_super_user_info = {
    "username": "user",
    "full_name": "user",
    "email": "user@example.com",
    "password": "123456",
    "status": "inactive",
    "is_superuser": True,
    "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
}


def get_superuser_token_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "email": fake_super_user_info["email"],
        "password": fake_super_user_info["password"],
    }
    response = client.post("/auth/token", data=login_data)
    tokens = response.json()
    print("\033[95m" + f"tokens: {tokens}" + "\033[m")
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers
