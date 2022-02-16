import enum
from datetime import datetime
from typing import Any, List, Optional, TypeVar, Dict
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
)
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.connection import Base, db
from app.common.const import get_settings
from app.models import User


settings = get_settings()


ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class StatusEnum(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2
    DISABLED = 3


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c
            for c in self.__table__.columns  # type: ignore
            if c.primary_key is False and c.name != "created_at"
        ]

    @classmethod
    def get(cls, session: Session, **kwargs) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.first()

    @classmethod
    def get_multi(
        cls, session: Session, skip: int = 0, limit: int = 100
    ) -> Optional[ModelType]:
        query = session.query(cls).offset(skip).limit(limit)
        return query.all() if query else None

    @classmethod
    def remove(cls, session: Session, **kwargs) -> ModelType:
        query = session.query(cls)
        for key, val in kwargs.items():
            query.filter(key == val)
        obj = query.delete()
        session.flush()
        session.commit()
        return obj

    @classmethod
    def update(cls, session: Session, id: int, auto_commit=True, **kwargs) -> Any:
        query = session.query(cls).filter(id == id).first()
        for key, val in kwargs.items():
            setattr(query, key, val)
        session.flush()
        if auto_commit:
            session.commit()
        return query

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
        return obj  # type: ignore


class Users(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

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
    __tablename__ = "dataset"

    root_path = Column(String(200), nullable=False, comment="/home/ihlee/Desktop")
    dataset_id = Column(String(50))
    zip_file_name = Column(String(50))


class Model(Base, BaseMixin):
    __tablename__ = "model"

    model_id = Column(String(50), nullable=False)
    model_name_kr = Column(String(50))
    model_name_en = Column(String(100))
    model_version = Column(String(50))
    model_path = Column(String(50))
    model_type = Column(String(50))


class Category(Base, BaseMixin):
    __tablename__ = "category"

    category_name_kr = Column(String(50), comment="카테고리명_한글")
    category_name_en = Column(String(100), comment="카테고리명_영문")
    category_code = Column(String(50), comment="고유서식코드")
    category_client_code = Column(String(50), comment="고유서식코드(고객응답용)")
    inference_doc_type = Column(String(50), comment="인퍼런스 결과(문서종류)")


class Image(Base, BaseMixin):
    __tablename__ = "image"

    image_id = Column(String(100), nullable=False, unique=True)
    image_path = Column(String(500), nullable=False)
    image_description = Column(String(50), nullable=True)
    create_datetime = Column(DateTime, default=datetime.now())


class Task(Base, BaseMixin):
    __tablename__ = "task"

    task_id = Column(String(100), nullable=False, unique=True)
    image_id = Column(ForeignKey("image.id"))
    category_id = Column(ForeignKey("category.id"))
    create_datetime = Column(DateTime, default=datetime.now())


class Inference(Base, BaseMixin):
    __tablename__ = "inference"
    __table_args__ = {"comment": "test1"}

    inference_id = Column(String(50), nullable=False)
    task_id = Column(ForeignKey("task.id"))
    inference_type = Column(String(5), comment="['cls', 'kv', 'gocr', 'reco']")
    inference_img_path = Column(String(300), nullable=False)
    inference_result = Column(JSON, nullable=True)
    start_datetime = Column(DateTime, nullable=True)
    finish_datetime = Column(DateTime, nullable=True)
    create_datetime = Column(DateTime, default=datetime.now())
    inference_sequence = Column(Integer, comment="inference 순서 1->2->3->4")


class Visualize(Base, BaseMixin):
    __tablename__ = "visualize"
    __table_args__ = {"extend_existing": True}

    task_id = Column(String(100), nullable=False)
    inference_type = Column(String(10), nullable=False, comment="['kv', 'gocr']")
    inference_img_path = Column(String(200), nullable=False)
    visualization_type = Column(String(20), nullable=True)


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
    category_name_kr        varchar(50)     NULL,
    category_name_en        varchar(100)    NULL,
    category_code           varchar(50)     NULL,
    category_client_code    varchar(50)     NULL,
    inference_doc_type      varchar(50)     NULL,
     PRIMARY KEY (pkey)
);

COMMENT ON COLUMN category.category_name_kr IS '카테고리명_한글';

COMMENT ON COLUMN category.category_name_en IS '카테고리명_영문';

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
    inference_id          varchar(50)     NULL,
    task_pkey             integer         NULL,
    inference_type        varchar(5)      NULL,
    inference_img_path    varchar(300)    NULL,
    inference_result      json            NULL,
    start_datetime        timestamp       NULL,
    finsh_datetime        timestamp       NULL,
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
