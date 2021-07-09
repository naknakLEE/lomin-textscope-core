from typing import Dict
from fastapi.testclient import TestClient


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
