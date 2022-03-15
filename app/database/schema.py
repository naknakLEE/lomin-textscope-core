import enum
import yaml
import typing
from datetime import datetime
from typing import Any, List, Optional, TypeVar, Dict, Union
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
    or_,
    Enum,
    Text
)
from sqlalchemy.orm import Session, relationship
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.connection import Base, db
from app.utils.logging import logger
from app.common.const import get_settings
from app.models import User

settings = get_settings()

ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

class StatusEnum(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2
    DISABLED = 3


exist_column_table = {
    "Dataset": "dataset_id",
    "Users": "email",
    "Model": "model_id",
    "Category": "category_name,dataset_pkey,model_pkey",
    "Image": "image_id,image_path",
    "Inference": "task_pkey,inference_type"
}

exist_column_message_table = {
    "Dataset": "dataset_id",
    "Users": "email",
    "Model": "model_id",
    "Category": "category_name,dataset_pkey,model_pkey",
    "Image": "image_id,image_path",
    "Inference": "task_pkey,inference_type"
}



class BaseMixin:
    # id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c
            for c in self.__table__.columns  # type: ignore
            if c.primary_key is False and c.name != "created_at"
        ]
    
    @classmethod
    def check_raw_exists(cls, session, kwargs):
        check_columns = exist_column_table.get(cls.__name__)
        message = ""
        if check_columns is None:
            return (message)
        inputs = {}
        for check_column in check_columns.split(","):
            inputs[check_column] = kwargs.get(check_column)
        is_exist = cls.get(session, **inputs)
        if is_exist:
            message = f"This {check_columns} already exist"
            logger.warning(f"{message}\n{yaml.dump([kwargs])}")
            return (message)
        return (message)

    @classmethod
    def get(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.first()

    @classmethod
    def get_multi(
        cls, session: Session, skip: int = 0, limit: int = 100, **kwargs
    ) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        query = query.offset(skip).limit(limit)
        return query.all() if query else None
    
    @classmethod
    def get_all(
        cls, session: Session, **kwargs
    ) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.all() if query else None

    @classmethod
    def remove(cls, session: Session, **kwargs: Dict) -> ModelType:
        query = session.query(cls)
        for key, val in kwargs.items():
            query.filter(key == val)
        obj = query.delete()
        session.flush()
        session.commit()
        return obj

    @typing.no_type_check
    @classmethod
    def update(
        cls, session: Session, id: int, auto_commit: bool = True, **kwargs: Any
    ) -> Optional[ModelType]:
        query = session.query(cls).filter(id == id).first()
        for key, val in kwargs.items():
            setattr(query, key, val)
        session.flush()
        if auto_commit:
            session.commit()
        return query

    @typing.no_type_check
    @classmethod
    def create(
        cls, session: Session, auto_commit: bool = True, **kwargs: Any
    ) -> Optional[ModelType]:
        check_result = cls.check_raw_exists(session, kwargs)
        if check_result:
            return check_result
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
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(length=128), nullable=True)
    email = Column(String(length=255), nullable=False)
    hashed_password = Column(String(length=2000), nullable=True)
    full_name = Column(String(length=128), nullable=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.INACTIVE.name)
    is_superuser = Column(Boolean, nullable=False, default=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    @classmethod
    def get_by_email(cls, session: Session, email: EmailStr) -> Optional[ModelType]:
        query = session.query(cls).filter(cls.email == email)
        return query.first()

    @classmethod
    def authenticate(cls, get_db: Session, email: str, password: str) -> Optional[User]:
        user = cls.get_by_email(get_db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

class Logs(Base, BaseMixin):
    __tablename__ = "logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(length=255), nullable=False)
    status_code = Column(Integer, nullable=False)

    @classmethod
    def get_usage_count(
        cls,
        session: Session,
        email: EmailStr = None,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> Dict:
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

class Dataset(Base, BaseMixin):
    __tablename__ = 'dataset'

    dataset_pkey = Column(Integer, primary_key=True)
    root_path = Column(String(200), nullable=False, comment='/home/ihlee/Desktop')
    dataset_id = Column(String(100))
    dataset_dir_name = Column(String(50))

    image = relationship('Image', back_populates='dataset')


class Model(Base, BaseMixin):
    __tablename__ = 'model'

    model_pkey = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False)
    model_name_kr = Column(String(50))
    model_name_en = Column(String(100))
    model_version = Column(String(50))
    model_path = Column(String(50))
    model_type = Column(String(50))
    create_datetime = Column(DateTime)

    category = relationship('Category', back_populates='model')


class Category(Base, BaseMixin):
    __tablename__ = 'category'

    category_pkey = Column(Integer, primary_key=True)
    category_name = Column(String(50), comment='category_a')
    category_code = Column(String(50))
    model_pkey = Column(ForeignKey('model.model_pkey'))
    dataset_pkey = Column(ForeignKey('dataset.dataset_pkey'))

    # dataset = relationship('Datset', back_populates='category')
    model = relationship('Model', back_populates='category')
    image = relationship('Image', back_populates='category')


# 중복된 데이터가 들어올 수 있으니 dataset pkey까지 사용해 저장 경로 만들도록 구성
class Image(Base, BaseMixin):
    __tablename__ = 'image'

    image_pkey = Column(Integer, primary_key=True, comment='1')
    image_id = Column(String(100), nullable=False, comment='uuuu-uuuu-uuuu-uuuu')
    image_path = Column(String(500), nullable=False, comment='/home/ihlee/Desktop/category_a/test.jpg')
    image_type = Column(String(30), nullable=False, comment="['TRAINING', 'INFERENCE']")
    image_description = Column(Text, comment='이미지 설명')
    category_pkey = Column(ForeignKey('category.category_pkey'), comment='category_a, 주민등록등본')
    dataset_pkey = Column(ForeignKey('dataset.dataset_pkey'))

    category = relationship('Category', back_populates='image')
    dataset = relationship('Dataset', back_populates='image')
    inference = relationship('Inference', back_populates='image')


class Task(Base, BaseMixin):
    __tablename__ = "task"

    task_pkey = Column(Integer, primary_key=True, comment='1')
    task_id = Column(String(100), nullable=False, unique=True)
    image_pkey = Column(ForeignKey("image.image_pkey"))
    task_type = Column(String(30), nullable=False, comment="TRAINING or INFERENCE")



class Inference(Base, BaseMixin):
    __tablename__ = 'inference'
    __table_args__ = {"extend_existing": True}

    inference_pkey = Column(Integer, primary_key=True)
    task_pkey = Column(ForeignKey("task.task_pkey"))
    image_pkey = Column(ForeignKey('image.image_pkey'))
    inference_type = Column(String(10), nullable=True, comment="['kv', 'gocr']")
    inference_results = Column(JSON)
    response_log = Column(JSON)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)

    image = relationship('Image', back_populates='inference')


class Visualize(Base, BaseMixin):
    __tablename__ = 'visualize'
    __table_args__ = {"extend_existing": True}

    visualize_pkey = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), nullable=False)
    inference_type = Column(String(50), nullable=False, comment="['kv', 'gocr']")
    inference_img_path = Column(String(200), nullable=False)

def create_db_table() -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
        Users.create(session, auto_commit=True, **settings.FAKE_SUPERUSER_INFORMATION)
        Users.create(session, auto_commit=True, **settings.FAKE_USER_INFORMATION)
        Users.create(session, auto_commit=True, **settings.FAKE_USER_INFORMATION_GUEST)
    finally:
        session.close()

"""
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
     PRIMARY KEY (model_pkey)
);

-- image Table Create SQL
CREATE TABLE image
(
    pkey                 integer         GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    image_id             varchar(50)     NOT NULL,
    image_path           varchar(300)    NULL,
    image_description    text            NULL,
    create_datetime      timestamp       NULL,
     PRIMARY KEY (pkey)
);

-- category Table Create SQL
CREATE TABLE category
(
    pkey                    integer         GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    category_name           varchar(50)     NULL,
    category_code           varchar(50)     NULL,
    category_client_code    varchar(50)     NULL,
    inference_doc_type      varchar(50)     NULL,
     PRIMARY KEY (pkey)
);

COMMENT ON COLUMN category.category_name IS '카테고리명';

COMMENT ON COLUMN category.category_code IS '고유서식코드';

COMMENT ON COLUMN category.category_client_code IS '고유서식코드(고객응답용)';

COMMENT ON COLUMN category.inference_doc_type IS '인퍼런스 결과(문서종류)';

-- task Table Create SQL
CREATE TABLE task
(
    pkey               integer        GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    task_id            varchar(50)    NOT NULL,id         integer        NULL,
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
    pkey                  integer         GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    task_pkey             integer         NULL,
    inference_type        varchar(5)      NULL,
    inference_img_path    varchar(300)    NULL,
    inference_result      json            NULL,
    start_datetime        timestamp       NULL,
    end_datetime        timestamp       NULL,
    create_datetime       timestamp       NULL,
    inference_sequence    integer         NULL,
     PRIMARY KEY (pkey)
);

COMMENT ON COLUMN inference.inference_type IS '[''cls'', ''kv'', ''gocr'', ''reco'']';

COMMENT ON COLUMN inference.inference_sequence IS 'inference 순서 1->2->3->4';

ALTER TABLE inference
    ADD CONSTRAINT FK_inference_task_pkey_task_pkey FOREIGN KEY (task_pkey)
        REFERENCES task (pkey);

"""