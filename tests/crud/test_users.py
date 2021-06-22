from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app.utils.auth import verify_password
from app.database.schema import UserUpdate, Users
from tests.utils.utils import random_email, random_lower_string


def test_create_user(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    # user_in = UserCreate(email=email, password=password)
    user = Users.create(get_db, email=email, password=password)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(email=email, password=password)
    authenticated_user = Users.authenticate(get_db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.authenticate(get_db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)
    is_active = Users.is_active(user)
    assert is_active is True


def test_check_if_user_is_active_inactive(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password, disabled=True)
    is_active = Users.is_active(user)
    assert is_superuser is False


def test_get_user(get_db: Session) -> None:
    EmailStr = random_lower_string()
    username = random_email()
    user = Users.create(get_db, email=username, is_superuser=True)
    is_superuser = Users.is_superuser(user)
    assert is_superuser is True


def test_check_if_user_is_superuser_normal_user(get_db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user = Users.create(email=username, password=password)
    is_superuser = Users.is_superuser(user)
    assert is_superuser is False


def test_get_user(get_db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=username, password=password, is_superuser=True)
    user_2 = Users.get(get_db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(get_db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user = Users.create(get_db, email=email, password=password, is_superuser=True)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    Users.update(get_db, db_obj=user, obj_in=user_in_update)
    user_2 = Users.get(get_db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
