import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Callable
from app.utils.auth import verify_password, get_password_hash
from app.database.schema import Users
from tests.utils.utils import (
    random_email,
    random_lower_string,
    check_superuser,
    check_status,
)


@pytest.mark.unit
@pytest.mark.usefixtures("get_db")
class TestUser:
    email: str
    password: str
    hashed_password: str

    def setup_method(self, method: Callable) -> None:
        self.email = random_email()
        self.password = random_lower_string()
        self.hashed_password = get_password_hash(self.password)

    def test_create_user(self, get_db: Session) -> None:
        data = {"email": self.email, "hashed_password": self.hashed_password}
        user = Users.create(get_db, **data)
        if user:
            assert user.email == self.email
            assert hasattr(user, "hashed_password")
            assert user.hashed_password is not None

    def test_authenticate_user(self, get_db: Session) -> None:
        data = {"email": self.email, "hashed_password": self.hashed_password}
        user = Users.create(get_db, **data)
        authenticated_user = Users.authenticate(
            get_db, email=self.email, password=self.password
        )
        if user and authenticated_user:
            print("\033[95m" + f"{user.__dict__}" + "\033[m")
            print("\033[95m" + f"{authenticated_user}" + "\033[m")
            assert authenticated_user
            assert user.email == authenticated_user.email

    def test_not_authenticate_user(self, get_db: Session) -> None:
        user = Users.authenticate(get_db, email=self.email, password=self.password)
        assert user is None

    def test_check_if_user_is_active(self, get_db: Session) -> None:
        data = {"email": self.email, "hashed_password": self.hashed_password}
        user = Users.create(get_db, **data)
        if user:
            status = check_status(user)
            assert status == "INACTIVE"

    def test_check_if_user_is_active_inactive(self, get_db: Session) -> None:
        data = {
            "email": self.email,
            "hashed_password": self.hashed_password,
            "status": "DISABLED",
        }
        user = Users.create(get_db, **data)
        if user:
            status = check_status(user)
            assert status == "DISABLED"

    def test_check_if_user_is_superuser_normal_user(self, get_db: Session) -> None:
        data = {"email": self.email, "hashed_password": self.hashed_password}
        user = Users.create(get_db, **data)
        if user:
            is_superuser = check_superuser(user)
            assert is_superuser is False

    def test_get_user(self, get_db: Session) -> None:
        data = {
            "email": self.email,
            "hashed_password": self.hashed_password,
            "is_superuser": True,
        }
        user = Users.create(get_db, **data)
        if user:
            user_2 = Users.get(get_db, id=user.id)
            assert user_2
            assert user.email == user_2.email
            assert jsonable_encoder(user) == jsonable_encoder(user_2)

    def test_update_user(self, get_db: Session) -> None:
        data = {
            "email": self.email,
            "hashed_password": self.hashed_password,
            "is_superuser": True,
        }
        user = Users.create(get_db, **data)
        new_password = random_lower_string()
        user_in_update = dict(
            email=self.email,
            hashed_password=get_password_hash(new_password),
            is_superuser=True,
        )
        if user:
            user = Users.update(get_db, id=user.id, **user_in_update)
            user_2 = Users.get(get_db, **dict(id=user.id))
            assert user_2
            assert user.email == user_2.email
            assert verify_password(new_password, user_2.hashed_password)
