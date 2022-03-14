import random
import string

from typing import Dict
from fastapi.testclient import TestClient

from typing import Dict
from app.common.const import get_settings
from app.database.schema import Users


settings = get_settings()
fake_super_user_info = {
    "username": "garam",
    "full_name": "garam",
    "email": "garam@example.com",
    "password": "123456",
    "status": "inactive",
    "is_superuser": False,
    "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
}


def random_string() -> str:
    characters = string.ascii_letters
    word_lenght = random.randint(0, 10)
    random_word_list = random.sample(characters, word_lenght)
    return "".join(random_word_list)


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def check_superuser(user: Users) -> bool:
    return user.is_superuser


def check_status(user: Users) -> str:
    return user.status.name


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
