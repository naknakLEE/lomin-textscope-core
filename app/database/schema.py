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

class HeungkukBaseMixin:
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

class Category(Base, HeungkukBaseMixin):
    __tablename__ = 'category'

    pkey = Column(Integer, primary_key=True)
    category_name_kr = Column(String(50), comment='카테고리명_한글')
    category_name_en = Column(String(50), comment='카테고리명_영문')
    category_code = Column(String(50), comment='고유서식코드')

    task = relationship('Task', back_populates='category')


class Image(Base, HeungkukBaseMixin):
    __tablename__ = 'image'

    pkey = Column(Integer, primary_key=True)
    image_id = Column(String(50), nullable=False)
    image_path = Column(String(50))
    image_description = Column(String(50))
    create_datetime = Column(DateTime)

    task = relationship('Task', back_populates='image')


class Task(Base, HeungkukBaseMixin):
    __tablename__ = 'task'

    pkey = Column(Integer, primary_key=True)
    task_id = Column(String(50), nullable=False)
    image_pkey = Column(ForeignKey('image.pkey'))
    category_pkey = Column(ForeignKey('category.pkey'))
    create_datetime = Column(DateTime)

    category = relationship('Category', back_populates='task')
    image = relationship('Image', back_populates='task')
    inference = relationship('Inference', back_populates='task')


class Inference(Base, HeungkukBaseMixin):
    __tablename__ = 'inference'

    pkey = Column(Integer, primary_key=True)
    inference_id = Column(String(50))
    task_pkey = Column(ForeignKey('task.pkey'))
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
    pkey                 integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    image_id             varchar(50)    NOT NULL, 
    image_path           varchar(50)    NULL, 
    image_description    varchar(50)    NULL, 
    create_datetime      timestamp      NULL, 
     PRIMARY KEY (pkey)
);


-- category Table Create SQL
CREATE TABLE category
(
    pkey                integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    category_name_kr    varchar(50)    NULL, 
    category_name_en    varchar(50)    NULL, 
    category_code       varchar(50)    NULL, 
     PRIMARY KEY (pkey)
);

COMMENT ON COLUMN category.category_name_kr IS '카테고리명_한글';

COMMENT ON COLUMN category.category_name_en IS '카테고리명_영문';

COMMENT ON COLUMN category.category_code IS '고유서식코드';


-- task Table Create SQL
CREATE TABLE task
(
    pkey               integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    task_id            varchar(50)    NOT NULL, 
    image_pkey         integer        NULL, 
    category_pkey      integer        NULL, 
    create_datetime    timestamp      NULL, 
     PRIMARY KEY (pkey)
);

ALTER TABLE task
    ADD CONSTRAINT FK_task_image_pkey_image_pkey FOREIGN KEY (image_pkey)
        REFERENCES image (pkey);

ALTER TABLE task
    ADD CONSTRAINT FK_task_category_pkey_category_pkey FOREIGN KEY (category_pkey)
        REFERENCES category (pkey);


-- inference Table Create SQL
CREATE TABLE inference
(
    pkey                  integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL, 
    inference_id          varchar(50)    NULL, 
    task_pkey             integer        NULL, 
    inference_type        varchar(5)     NULL, 
    inference_img_path    varchar(50)    NULL, 
    inference_result      json           NULL, 
    start_datetime        timestamp      NULL, 
    finsh_datetime        timestamp      NULL, 
    create_datetime       timestamp      NULL, 
    inference_sequence    integer        NULL, 
     PRIMARY KEY (pkey)
);

COMMENT ON COLUMN inference.inference_type IS '[''cls'', ''kv'', ''gocr'', ''reco'']';

COMMENT ON COLUMN inference.inference_sequence IS 'inference 순서 1->2->3->4';

ALTER TABLE inference
    ADD CONSTRAINT FK_inference_task_pkey_task_pkey FOREIGN KEY (task_pkey)
        REFERENCES task (pkey);

'''
