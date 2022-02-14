import random
import string
import json

from typing import Dict
from fastapi.testclient import TestClient
from fastapi import status

from typing import Dict, Callable, Any
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


class Assert:
    func: Callable
    data: Dict
    _input: Dict
    _expected: Dict
    _output: Any

    def __init__(self, func: Callable, data: Dict = {}):
        self.func = func  # type: ignore
        self.data = data
        self._input = data.get("input", {})
        self._expected = data.get("expected", {})
        self._output = self.func(**self._input) if self.data else self.func()

    def equal(self):
        assert self._expected == self._output, (self._input, self._output)

    def equal_response(self):
        assert self._output.status_code == status.HTTP_200_OK, (
            self._input,
            self._output,
        )
        output_body = self._output
        expected_body = self._expected
        if isinstance(self._output.body, bytes):
            output_body = json.loads(output_body.body)
            expected_body = json.loads(expected_body.body)
        elif hasattr(self._output, "json"):
            output_body = output_body.json()
            expected_body = expected_body.json()
        assert output_body == expected_body, (self._input, self._output)

    def not_equal(self):
        assert self._expected != self._output, (self._input, self._output)

    def is_none(self):
        assert self._output is None, (self._input, self._output)

    def is_not_none(self):
        assert self._output is not None, (self._input, self._output)

    def is_instance(self, _type: Any):
        assert isinstance(self._output, _type), (self._input, self._output)
