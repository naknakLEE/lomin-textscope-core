from configparser import Error
import json
import enum

from datetime import datetime
from logging import disable
from typing import Any, Dict, Union, Optional, List, TypeVar
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    DateTime,
    func,
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    Text,
    and_,
    or_,
)
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql.sqltypes import BIGINT
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.connection import Base, db
from app.common.const import get_settings
from app.models import UserUpdate, User, UsersScheme, UserInDB


ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


class StatusEnum(enum.Enum):
    active = 1
    inactive = 2
    disabled = 3


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c
            for c in self.__table__.columns
            if c.primary_key is False and c.name != "created_at"
        ]

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
        cls, session: Session, skip: int = 0, limit: int = 100
    ) -> Optional[ModelType]:
        query = session.query(cls).offset(skip).limit(limit)
        return query.all()

    @classmethod
    def get_by_email(cls, session: Session, email: EmailStr) -> Optional[ModelType]:
        query = session.query(cls).filter(cls.email == email)
        return query.first()

    @classmethod
    def remove(cls, session: Session, email: EmailStr) -> ModelType:
        obj = session.query(cls).filter(cls.email == email).delete()
        session.flush()
        session.commit()
        return obj

    @classmethod
    def update(cls, session: Session, *, db_obj: User, obj_in: UserInDB) -> Any:
        current_user_email = db_obj.email
        obj_in.hashed_password = get_password_hash(obj_in.password)
        obj_data = jsonable_encoder(db_obj)
        user = session.query(cls).filter(cls.email == current_user_email).first()
        for field in obj_data:
            field_value = getattr(obj_in, field) if hasattr(obj_in, field) else None
            if field_value is not None:
                setattr(user, field, field_value)
        session.flush()
        session.commit()
        return user

    @classmethod
    def create(
        cls, session: Session, auto_commit=True, **kwargs
    ) -> Optional[ModelType]:
        is_exist = cls.get_by_email(session, email=kwargs["email"])
        if is_exist:
            return "This user already exist"
        kwargs["hashed_password"] = get_password_hash(kwargs["password"])

        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        # session.refresh(obj)
        return obj

    @classmethod
    def create_log(
        cls, session: Session, auto_commit=True, **kwargs
    ) -> Optional[ModelType]:
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        # session.refresh(obj)
        return obj

    @classmethod
    def authenticate(
        cls, get_db: Session, *, email: str, password: str
    ) -> Optional[User]:
        user = cls.get_by_email(get_db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def get_usage_count(
        cls,
        session: Session,
        email: EmailStr = None,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> Optional[ModelType]:
        if email is not None:
            query = (
                session.query(func.count(cls.status_code))
                .filter(cls.email == email)
                .group_by(cls.status_code)
            )
        else:
            query = session.query(func.count(cls.email))

        if start_time is not None and end_time is not None:
            query = query.filter(
                and_(cls.created_at <= end_time, cls.created_at >= start_time)
            )
        elif start_time is not None:
            query = query.filter(cls.created_at >= start_time)
        elif end_time is not None:
            query = query.filter(cls.created_at <= end_time)

        success_response = query.filter(
            and_(cls.status_code < 300, cls.status_code >= 200)
        )
        failed_response = query.filter(
            or_(cls.status_code >= 300, cls.status_code < 200)
        )
        return {
            "success_response": success_response.all(),
            "failed_response": failed_response.all(),
        }

    @classmethod
    def get_usage(
        cls,
        session: Session,
        email: EmailStr = None,
        skip: int = 0,
        limit: int = 100,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> Optional[ModelType]:
        query = session.query(cls)
        if start_time is not None and end_time is not None:
            query = query.filter(
                and_(cls.created_at <= end_time, cls.created_at >= start_time)
            )
        elif start_time is not None:
            query = query.filter(cls.created_at >= start_time)
        elif end_time is not None:
            query = query.filter(cls.created_at <= end_time)

        if email is not None:
            query = query.filter(cls.email == email)
        else:
            query = query.offset(skip).limit(limit)

        return query.all()

class WooriBaseMixin:
    def all_columns(self) -> List:
        return [
            c
            for c in self.__table__.columns
            if c.primary_key is False and c.name != "created_at"
        ]

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
        cls, session: Session, skip: int = 0, limit: int = 100
    ) -> Optional[ModelType]:
        query = session.query(cls).offset(skip).limit(limit)
        return query.all()

    @classmethod
    def remove(cls, session: Session, email: EmailStr) -> ModelType:
        obj = session.query(cls).filter(cls.email == email).delete()
        session.flush()
        session.commit()
        return obj

    @classmethod
    def update(cls, session: Session, *, obj_in) -> Any:
        task_id = obj_in["task_id"]
        model = session.query(cls).filter(cls.task_id == task_id).first()
        for key, value in obj_in.items():
            setattr(model, key, value)
        session.flush()
        session.commit()
        return model
    
    @classmethod
    def image_update(cls, session: Session, **kwargs) -> Any:
        image_id = kwargs["image_id"]
        model = session.query(cls).filter(cls.image_id == image_id).first()
        for key, value in kwargs.items():
            setattr(model, key, value)
        session.flush()
        session.commit()
        return model

    @classmethod
    def create(
        cls, session: Session, auto_commit=True, **kwargs
    ) -> Optional[ModelType]:
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        # session.refresh(obj)
        return obj

class Category(Base):
    __tablename__ = 'category'

    category_peky = Column(Integer, primary_key=True)
    category_name_kr = Column(String(50), comment='카테고리명_한글')
    category_name_en = Column(String(50), comment='카테고리명_영문')
    category_code = Column(String(50), comment='고유서식코드')

    task = relationship('Task', back_populates='category')


class Image(Base):
    __tablename__ = 'image'

    image_pkey = Column(Integer, primary_key=True)
    image_id = Column(String(50), nullable=False)
    image_path = Column(String(50))
    image_description = Column(String(50))
    create_datetime = Column(DateTime)

    task = relationship('Task', back_populates='image')


class Task(Base):
    __tablename__ = 'task'

    task_pkey = Column(Integer, primary_key=True)
    task_id = Column(String(50), nullable=False)
    image_pkey = Column(ForeignKey('image.image_pkey'))
    category_peky = Column(ForeignKey('category.category_peky'))
    create_datetime = Column(DateTime)

    category = relationship('Category', back_populates='task')
    image = relationship('Image', back_populates='task')
    inference = relationship('Inference', back_populates='task')


class Inference(Base):
    __tablename__ = 'inference'

    inference_pkey = Column(Integer, primary_key=True)
    inference_id = Column(String(50))
    task_pkey = Column(ForeignKey('task.task_pkey'))
    inference_type = Column(String(5), comment="['cls', 'kv', 'gocr', 'reco']")
    inference_img_path = Column(String(50))
    inference_result = Column(JSON)
    start_datetime = Column(DateTime)
    finsh_datetime = Column(DateTime)
    create_datetime = Column(DateTime)
    inference_sequence = Column(Integer, comment='inference 순서 1->2->3->4')

    task = relationship('Task', back_populates='inference')





'''

-- image Table Create SQL
CREATE TABLE image
(
    image_pkey           integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    image_id             varchar(50)    NOT NULL, 
    image_path           varchar(50)    NULL, 
    image_description    varchar(50)    NULL, 
    create_datetime      timestamp      NULL, 
     PRIMARY KEY (image_pkey)
);


-- category Table Create SQL
CREATE TABLE category
(
    category_peky       integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    category_name_kr    varchar(50)    NULL, 
    category_name_en    varchar(50)    NULL, 
    category_code       varchar(50)    NULL, 
     PRIMARY KEY (category_peky)
);

COMMENT ON COLUMN category.category_name_kr IS '카테고리명_한글';

COMMENT ON COLUMN category.category_name_en IS '카테고리명_영문';

COMMENT ON COLUMN category.category_code IS '고유서식코드';


-- task Table Create SQL
CREATE TABLE task
(
    task_pkey          integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    task_id            varchar(50)    NOT NULL, 
    image_pkey         integer        NULL, 
    category_peky      integer        NULL, 
    create_datetime    timestamp      NULL, 
     PRIMARY KEY (task_pkey)
);

ALTER TABLE task
    ADD CONSTRAINT FK_task_image_pkey_image_image_pkey FOREIGN KEY (image_pkey)
        REFERENCES image (image_pkey);

ALTER TABLE task
    ADD CONSTRAINT FK_task_category_peky_category_category_peky FOREIGN KEY (category_peky)
        REFERENCES category (category_peky);


-- inference Table Create SQL
CREATE TABLE inference
(
    inference_pkey        integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    inference_id          varchar(50)    NULL, 
    task_pkey             integer        NULL, 
    inference_type        varchar(5)     NULL, 
    inference_img_path    varchar(50)    NULL, 
    inference_result      json           NULL, 
    start_datetime        timestamp      NULL, 
    finsh_datetime        timestamp      NULL, 
    create_datetime       timestamp      NULL, 
    inference_sequence    integer        NULL, 
     PRIMARY KEY (inference_pkey)
);

COMMENT ON COLUMN inference.inference_type IS '[''cls'', ''kv'', ''gocr'', ''reco'']';

COMMENT ON COLUMN inference.inference_sequence IS 'inference 순서 1->2->3->4';

ALTER TABLE inference
    ADD CONSTRAINT FK_inference_task_pkey_task_task_pkey FOREIGN KEY (task_pkey)
        REFERENCES task (task_pkey);
'''
