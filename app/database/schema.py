import json
from typing import Any, Dict, Union

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import Session, relationships
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext

from app.database.connection import Base, db
from app.common.const import get_settings
from app.models import UserUpdate, User


# 왜 app.utils.auth에서 import 안되는가?
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self):
        return [c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"]

    def __hash__(self):
        hash(self.id)

    @classmethod
    def get(cls, **kwargs):
        session = next(db.session())
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        # if query.count() > 1:
        #     raise Exception("Only one row is supposed to be returned, but got more than one.")
        return query.first()


    @classmethod
    def get_multi(cls, session: Session, skip: int = 0, limit: int = 100):
        session = next(db.session())
        query = session.query(cls).offset(skip).limit(limit).all()
        return query


    @classmethod
    def get_by_email(cls, session: Session, *, email: str):
        session = next(db.session())
        query = session.query(cls).filter(cls.email == email)
        return query.first()


    @classmethod
    def remove(cls, session: Session, email: str):
        obj = session.query(cls).filter(cls.email==email).delete()
        session.flush()
        session.commit()
        return obj


    @classmethod
    def update(
        cls, session: Session, *, db_obj: User, obj_in: UserUpdate
    ):
        is_exist = cls.get_by_email(session, email=obj_in.email)
        if is_exist:
            return "This user already exist"
        current_user_email = db_obj.email
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            value = getattr(obj_in, field)
            if value is not None:
                setattr(db_obj, field, value)
        user = session.query(cls).filter(cls.email == current_user_email)
        user.update(db_obj)
        session.flush()
        session.commit()
        return db_obj


    @classmethod
    def create(cls, session: Session, auto_commit=False, **kwargs):
        is_exist = cls.get_by_email(session, email=kwargs["email"])
        if is_exist:
            return "This user already exist"
        
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        return obj


class Users(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True} 
    username = Column(String(length=128), nullable=True)
    email = Column(String(length=255), nullable=True)
    hashed_password = Column(String(length=2000), nullable=True)
    full_name = Column(String(length=128), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Errors(Base, BaseMixin):
    __tablename__ = "errors"
    __table_args__ = {'extend_existing': True} 
    url = Column(String(length=2000), nullable=True)
    method = Column(String(length=255), nullable=True)
    status_code = Column(String(length=255), nullable=True)
    error_detail = Column(String(length=2000), nullable=True)
    client = Column(String(length=2000), nullable=True)
    processed_time = Column(String(length=255), nullable=True)
    datetime_kr = Column(String(length=255), nullable=True)


class Logs(Base, BaseMixin):
    __tablename__ = "logs"
    __table_args__ = {'extend_existing': True} 
    url = Column(String(length=2000), nullable=True)
    method = Column(String(length=255), nullable=True)
    status_code = Column(String(length=255), nullable=True)
    log_detail = Column(String(length=2000), nullable=True)
    error_detail = Column(JSON, nullable=True)
    client = Column(String(length=2000), nullable=True)
    request_timestamp = Column(String(length=255), nullable=True)
    response_timestamp = Column(String(length=255), nullable=True)
    processed_time = Column(String(length=255), nullable=True)


class Usage(Base, BaseMixin):
    __tablename__ = "usage"
    __table_args__ = {'extend_existing': True} 
    # choose email or id ??
    email = Column(String(length=255), nullable=True)
    status_code = Column(Integer, nullable=True)


def create_db_table():
    try:
        settings = get_settings()
        session = next(db.session())
        Usage.metadata.create_all(db._engine)
        Errors.metadata.create_all(db._engine)
        Logs.metadata.create_all(db._engine)
        Users.metadata.create_all(db._engine)
        Users.create(session, auto_commit=True, name="test", **settings.FAKE_INFORMATION)
    finally:
        session.close()