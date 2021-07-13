import os
import pytest

from typing import Dict
from fastapi.testclient import TestClient
from httpx import AsyncClient

from kakaobank_wrapper.app.main import create_app
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session")
def app():
    os.environ["API_ENV"] = "test"
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app=app)


@pytest.fixture(scope="module")
def user_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)
