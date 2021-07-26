from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app.utils.auth import verify_password
from app.database.schema import Users
from app.models import UsersScheme, UserInDB
from tests.utils.utils import (
    random_email,
    random_lower_string,
    check_superuser,
    check_status,
)


def test_create_user(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password)
    authenticated_user = Users.authenticate(get_db, email=email, password=password)
    print("\033[95m" + f"{user.__dict__}" + "\033[m")
    print("\033[95m" + f"{authenticated_user}" + "\033[m")
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
    status = check_status(user)
    assert status == "inactive"


def test_check_if_user_is_active_inactive(get_db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=email, password=password, status="disabled")
    status = check_status(user)
    assert status == "disabled"


def test_get_user(get_db: Session) -> None:
    EmailStr = random_lower_string()
    username = random_email()
    user = Users.create(get_db, email=username, is_superuser=True)
    is_superuser = check_superuser(user)
    assert is_superuser is True


def test_check_if_user_is_superuser_normal_user(get_db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user = Users.create(get_db, email=username, password=password)
    is_superuser = check_superuser(user)
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
    user_in_update = UserInDB(email=email, password=new_password, is_superuser=True)
    Users.update(get_db, db_obj=user, obj_in=user_in_update)
    user_2 = Users.get(get_db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
