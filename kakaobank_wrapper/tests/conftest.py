import os
import pytest

from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from kakaobank_wrapper.app.main import create_app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers
from app.common.const import get_settings


settings = get_settings()
fake_user_info = settings.FAKE_USER_INFORMATION


@pytest.fixture(scope="session")
def app():
    os.environ["API_ENV"] = "test"
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app=app)


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, get_db: Session) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client,
        email=fake_user_info["email"],
        get_db=get_db,
    )
