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



class Users(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    username = Column(String(length=128), nullable=True)
    email = Column(String(length=255), nullable=False)
    hashed_password = Column(String(length=2000), nullable=True)
    full_name = Column(String(length=128), nullable=True)
    status = Column(Enum(StatusEnum), nullable=False, default="inactive")
    is_superuser = Column(Boolean, nullable=False, default=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class Logs(Base, BaseMixin):
    __tablename__ = "logs"
    __table_args__ = {"extend_existing": True}
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
    __table_args__ = {"extend_existing": True}
    email = Column(String(length=255), nullable=False)
    status_code = Column(Integer, nullable=False)

class Dataset(Base, WooriBaseMixin):
    __tablename__ = 'dataset'

    dataset_pkey = Column(Integer, primary_key=True)
    root_path = Column(String(200), nullable=False, comment='/home/ihlee/Desktop')
    dataset_id = Column(String(50))
    zip_file_name = Column(String(50))

    image = relationship('Image', back_populates='dataset')


class Model(Base, WooriBaseMixin):
    __tablename__ = 'model'

    model_pkey = Column(Integer, primary_key=True)
    model_id = Column(String(50), nullable=False)
    model_name_kr = Column(String(50))
    model_name_en = Column(String(100))
    model_version = Column(String(50))
    model_path = Column(String(50))
    model_type = Column(String(50))
    create_datetime = Column(DateTime)

    category = relationship('Category', back_populates='model')


class Category(Base, WooriBaseMixin):
    __tablename__ = 'category'

    category_pkey = Column(Integer, primary_key=True)
    category_name_en = Column(String(50), comment='category_a')
    category_name_kr = Column(String(50), comment='주민등록등본')
    model_pkey = Column(ForeignKey('model.model_pkey'))
    category_code = Column(String(50))

    model = relationship('Model', back_populates='category')
    image = relationship('Image', back_populates='category')


class Image(Base, WooriBaseMixin):
    __tablename__ = 'image'

    image_pkey = Column(Integer, primary_key=True, comment='1')
    image_id = Column(String(50), nullable=False, comment='uuuu-uuuu-uuuu-uuuu')
    image_path = Column(String(200), nullable=False, comment='/home/ihlee/Desktop/category_a/test.jpg')
    image_type = Column(String(30), nullable=False, comment="['training', 'inference']")
    image_description = Column(Text, comment='이미지 설명')
    category_pkey = Column(ForeignKey('category.category_pkey'), comment='category_a, 주민등록등본')
    dataset_pkey = Column(ForeignKey('dataset.dataset_pkey'))

    category = relationship('Category', back_populates='image')
    dataset = relationship('Dataset', back_populates='image')
    inference = relationship('Inference', back_populates='image')


class Inference(Base, WooriBaseMixin):
    __tablename__ = 'inference'
    __table_args__ = {'comment': 'test1'}

    inference_pkey = Column(Integer, primary_key=True)
    task_id = Column(String(50), nullable=False)
    inference_type = Column(String(5), nullable=False, comment="['kv', 'gocr']")
    create_datetime = Column(DateTime, nullable=True)
    inference_result = Column(JSON)
    image_pkey = Column(ForeignKey('image.image_pkey'))
    start_datetime = Column(DateTime, nullable=True)
    finsh_datetime = Column(DateTime, nullable=True)
    inference_img_path = Column(String(200), nullable=True)

    image = relationship('Image', back_populates='inference')


class Visualize(Base, WooriBaseMixin):
    __tablename__ = 'visualize'
    __table_args__ = {"extend_existing": True}

    visualize_pkey = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False)
    inference_type = Column(String(5), nullable=False, comment="['kv', 'gocr']")
    inference_img_path = Column(String(200), nullable=False)


'''
﻿-- The table order was sorted considering the relationship to prevent error from occurring if all are run at once.

-- model Table Create SQL
CREATE TABLE model
(
    model_pkey         int             GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    model_id           varchar(50)     NOT NULL, 
    model_name_kr      varchar(50)     NULL, 
    model_name_en      varchar(100)    NULL, 
    model_version      varchar(50)     NULL, 
    model_path         varchar(50)     NULL, 
    model_type         varchar(50)     NULL, 
    create_datetime    timestamp       NULL, 
     PRIMARY KEY (model_pkey)
);


-- dataset Table Create SQL
CREATE TABLE dataset
(
    dataset_pkey     int             GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    dataset_id       varchar(50)     NULL, 
    root_path        varchar(200)    NOT NULL, 
    zip_file_name    varchar(50)     NULL, 
     PRIMARY KEY (dataset_pkey)
);

COMMENT ON COLUMN dataset.root_path IS '/home/ihlee/Desktop';


-- category Table Create SQL
CREATE TABLE category
(
    category_pkey       int            GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    category_name_en    varchar(50)    NULL, 
    category_name_kr    varchar(50)    NULL, 
    model_pkey          integer        NULL, 
    category_code       varchar(50)    NULL, 
     PRIMARY KEY (category_pkey)
);

COMMENT ON COLUMN category.category_name_en IS 'category_a';

COMMENT ON COLUMN category.category_name_kr IS '주민등록등본';

COMMENT ON COLUMN category.category_code IS 'A01';

ALTER TABLE category
    ADD CONSTRAINT FK_category_model_pkey_model_model_pkey FOREIGN KEY (model_pkey)
        REFERENCES model (model_pkey);


-- image Table Create SQL
CREATE TABLE image
(
    image_pkey           int             GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    image_id             varchar(50)     NOT NULL, 
    image_path           varchar(200)    NOT NULL, 
    image_description    text            NULL, 
    category_pkey        integer         NULL, 
    dataset_pkey         integer         NULL, 
    image_type           varchar(30)     NOT NULL, 
     PRIMARY KEY (image_pkey)
);

COMMENT ON COLUMN image.image_pkey IS '1';

COMMENT ON COLUMN image.image_id IS 'uuuu-uuuu-uuuu-uuuu';

COMMENT ON COLUMN image.image_path IS '/home/ihlee/Desktop/category_a/test.jpg';

COMMENT ON COLUMN image.image_description IS '이미지 설명';

COMMENT ON COLUMN image.category_pkey IS 'category_a, 주민등록등본';

COMMENT ON COLUMN image.image_type IS '[''training'', ''inference'']';

ALTER TABLE image
    ADD CONSTRAINT FK_image_category_pkey_category_category_pkey FOREIGN KEY (category_pkey)
        REFERENCES category (category_pkey);

ALTER TABLE image
    ADD CONSTRAINT FK_image_dataset_pkey_dataset_dataset_pkey FOREIGN KEY (dataset_pkey)
        REFERENCES dataset (dataset_pkey);


-- inference Table Create SQL
CREATE TABLE inference
(
    inference_pkey        int            GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    task_id               varchar(50)    NOT NULL, 
    inference_result      json           NULL, 
    inference_type        varchar(5)     NOT NULL, 
    create_datetime       timestamp      NULL, 
    image_pkey            integer        NULL, 
    start_datetime        timestamp      NULL, 
    finsh_datetime        timestamp      NULL, 
    inference_img_path    varchar(50)    NULL, 
     PRIMARY KEY (inference_pkey)
);

COMMENT ON TABLE inference IS 'test1';

COMMENT ON COLUMN inference.inference_type IS '[''kv'', ''gocr'']';

ALTER TABLE inference
    ADD CONSTRAINT FK_inference_image_pkey_image_image_pkey FOREIGN KEY (image_pkey)
        REFERENCES image (image_pkey);



'''

# def create_db_table() -> None:
#     try:
#         settings = get_settings()
#         session = next(db.session())
#         Base.metadata.create_all(db._engine)
#         Users.create(session, auto_commit=True, **settings.FAKE_SUPERUSER_INFORMATION)
#         Users.create(session, auto_commit=True, **settings.FAKE_USER_INFORMATION)
#     finally:
#         session.close()
