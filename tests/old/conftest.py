import os
os.environ["API_ENV"] = "test"
import pytest

from typing import Dict, Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.utils.create_app import app_generator
from app.database.connection import Base, db
from tests.utils.user import get_superuser_token_headers, get_normaluser_token_headers
from app.common.const import get_settings
from sqlalchemy import create_engine
from app.database import schema
from _pytest.fixtures import SubRequest
from _pytest.config.argparsing import Parser


settings = get_settings()
fake_user_info = settings.FAKE_NORMALUSER_INFORMATION


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--max",
        action="store",
        default=1,
        type=int,
        help="execute total testcase count default: 1",
    )
    parser.addoption(
        "--base-path",
        action="store",
        default="/workspace/tests",
        type=str,
        help="root path include test code",
    )


@pytest.fixture(scope="session", autouse=False)
def testcase_limit(request: SubRequest) -> int:
    return request.config.getoption("--max")


@pytest.fixture(scope="session", autouse=False)
def base_path(request: SubRequest) -> str:
    return request.config.getoption("--base-path")


@pytest.fixture(scope="session", autouse=False)
def get_db() -> Generator:
    engine = create_engine("sqlite:////workspace/tests/resources/test.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    schema.Base.metadata.create_all(bind=engine)
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=False)
def app() -> FastAPI:
    return app_generator()


@pytest.fixture(scope="session", autouse=False)
def client(app: FastAPI) -> TestClient:
    Base.metadata.create_all(db._engine)
    return TestClient(app=app)


@pytest.fixture(scope="module", autouse=False)
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module", autouse=False)
def normal_user_token_headers(client: TestClient) -> Dict[str, str]:
    return get_normaluser_token_headers(client)
