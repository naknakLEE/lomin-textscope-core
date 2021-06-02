from typing import Dict

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.append("/workspace")
from app.main import create_app
from app.database.connection import Base, db
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from app.common.const import get_settings


settings = get_settings()
fake_user_info = settings.FAKE_USER_INFORMATION


@pytest.fixture(scope="session")
def get_db():
    db_session = db._session()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture(scope="session")
def app():
    os.environ["API_ENV"] = "test"
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    Base.metadata.create_all(db._engine)
    return TestClient(app=app)


@pytest.fixture(scope="module")
def superuser_token(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token(client: TestClient, get_db: Session) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client, email=fake_user_info["email"], db=get_db
    )


# @pytest.fixture(scope="function", autouse=True)
# def session():
#     sess = next(db.session())
#     yield sess
#     clear_all_table_data(
#         session=sess,
#         metadata=Base.metadata,
#         except_tables=[]
#     )
#     sess.rollback()


# @pytest.fixture(scope="function")
# def login(session):
#     db_user = Users.create(session=session, email="shinuk@example.com", pw="123456")
#     session.commit()
#     access_token = create_access_token(data=UserToken.from_orm(db_user).dict(exclude={'pw', 'marketing_agree'}),)
#     return dict(Authorization=f"Bearer {access_token}")


# def clear_all_table_data(session: Session, metadata, except_tables: List[str] = None):
#     session.excute("SET FOREIGN_KEY_CHECKS = 0;")
#     for table in metadata.sorted_tables:
#         if table.name not in except_tables:
#             session.execute(table.delete())
#     session.execute("SET FOREIGN_KEY_CHECKS = 1;")
#     session.commit()
