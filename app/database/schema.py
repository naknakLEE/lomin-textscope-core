import json

from logging import disable
from typing import Any, Dict, Union, Optional, List, TypeVar
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    JSON,
    Boolean,
    ForeignKey,
    and_,
    or_
)
from sqlalchemy.orm import Session, relationships
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.connection import Base, db
from app.common.const import get_settings
from app.models import UserUpdate, User


ModelType = TypeVar("ModelType", bound=Base)


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"]


    @classmethod
    def get(cls, session: Session = None, **kwargs) -> Optional[ModelType]:
        sess = next(db.session()) if not session else session

        query = sess.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        if sess is None:
            sess.close()
        # if query.count() > 1:
        #     raise Exception("Only one row is supposed to be returned, but got more than one.")
        return query.first()


    @classmethod
    def get_multi(
        cls, 
        session: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> Optional[ModelType]:
        query = session.query(cls).offset(skip).limit(limit)
        return query.all()


    @classmethod
    def get_by_email(cls, 
        session: Session, 
        email: EmailStr
) -> Optional[ModelType]:
        query = session.query(cls).filter(cls.email == email)
        return query.first()


    @classmethod
    def remove(cls, session: Session, email: EmailStr) -> ModelType:
        obj = session.query(cls).filter(cls.email==email).delete()
        session.flush()
        session.commit()
        return obj


    @classmethod
    def update(
        cls, 
        session: Session, 
        *, 
        db_obj: User, 
        obj_in: UserUpdate
    ) -> ModelType:
        is_exist = cls.get_by_email(session, email=obj_in.email)
        if is_exist:
            return "This user already exist"
        current_user_email = db_obj.email
        obj_data = jsonable_encoder(db_obj)
        user = session.query(cls).filter(cls.email == current_user_email).first()
        for field in obj_data:
            field_value = getattr(obj_in, field)
            if field_value is not None:
                setattr(user, field, field_value)
        session.flush()
        session.commit()
        return user


    @classmethod
    def create(
        cls, 
        session: Session, 
        auto_commit=True, 
        **kwargs
    ) -> Optional[ModelType]:
        is_exist = cls.get_by_email(session, email=kwargs["email"])
        if is_exist:
            return "This user already exist"
        
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        user = User(email=obj.email)
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        # session.refresh(obj)
        return user

    @classmethod
    def create_usage(cls, 
        session: Session, 
        auto_commit=True, 
        **kwargs
    ) -> ModelType:
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        user = User(email=obj.email)
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        # session.refresh(obj)
        return user


class Users(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True} 
    username = Column(String(length=128), nullable=True)
    email = Column(String(length=255), nullable=False, primary_key=True)
    hashed_password = Column(String(length=2000), nullable=True)
    full_name = Column(String(length=128), nullable=True)
    disabled = Column(Boolean, nullable=True, default=False)
    is_active = Column(Boolean, nullable=True, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Logs(Base, BaseMixin):
    __tablename__ = "logs"
    __table_args__ = {'extend_existing': True} 
    url = Column(String(length=2000), nullable=False)
    method = Column(String(length=255), nullable=False)
    status_code = Column(String(length=255), nullable=False)
    log_detail = Column(String(length=2000), nullable=True)
    error_detail = Column(JSON, nullable=True)
    client = Column(String(length=2000), nullable=True)
    request_timestamp = Column(String(length=255), nullable=False)
    response_timestamp = Column(String(length=255), nullable=False)
    processed_time = Column(String(length=255), nullable=False)


class Usage(Base, BaseMixin):
    __tablename__ = "usage"
    __table_args__ = {'extend_existing': True} 
    email = Column(String(length=255), nullable=False)
    status_code = Column(Integer, nullable=False)

    @classmethod
    def get_usage(cls, session: Session, email: EmailStr = None) -> Optional[ModelType]:
        if email is not None:
            query = session.query(cls.status_code, cls.created_at).filter(cls.email == email)
        else:
            query = session.query(cls.email, func.count(cls.email)).group_by(cls.email)
            
        success_response = query.filter(and_(cls.status_code < 300, cls.status_code >= 200))
        failed_response = query.filter(or_(cls.status_code >= 300, cls.status_code < 200))
        return { 
            # "total_response": query.all(),
            "success_response": success_response.all(), 
            "failed_response": failed_response.all(),
        }


def create_db_table() -> None:
    try:
        settings = get_settings()
        session = next(db.session())
        Base.metadata.create_all(db._engine)
        Users.create(session, auto_commit=True, **settings.FAKE_SUPERUSER_INFORMATION)
        Users.create(session, auto_commit=True, **settings.FAKE_USER_INFORMATION)
    finally:
        session.close()
