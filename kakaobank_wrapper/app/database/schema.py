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
    DATETIME,
    Time,
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    and_,
    or_,
)
from sqlalchemy.orm import Session, relationships
from sqlalchemy.sql.sqltypes import BIGINT
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.common.const import get_settings
from app.models import UserUpdate, User, UsersScheme, UserInDB
from kakaobank_wrapper.app.database.connection import Base, db


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


class ResultClsEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D03 = 3
    D04 = 4


class ReCogYnEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D03 = 3
    D04 = 4


class ErrorCodeEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D03 = 3
    D04 = 4


class ModelTypeEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D03 = 3
    D04 = 4


class BaseMixin:
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"
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
    def get_multi(cls, session: Session, skip: int = 0, limit: int = 100) -> Optional[ModelType]:
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
    def create(cls, session: Session, auto_commit=True, **kwargs) -> Optional[ModelType]:
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
    def create_usage(cls, session: Session, auto_commit=True, **kwargs) -> ModelType:
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
    def authenticate(cls, get_db: Session, *, email: str, password: str) -> Optional[User]:
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
            query = query.filter(and_(cls.created_at <= end_time, cls.created_at >= start_time))
        elif start_time is not None:
            query = query.filter(cls.created_at >= start_time)
        elif end_time is not None:
            query = query.filter(cls.created_at <= end_time)

        success_response = query.filter(and_(cls.status_code < 300, cls.status_code >= 200))
        failed_response = query.filter(or_(cls.status_code >= 300, cls.status_code < 200))
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
            query = query.filter(and_(cls.created_at <= end_time, cls.created_at >= start_time))
        elif start_time is not None:
            query = query.filter(cls.created_at >= start_time)
        elif end_time is not None:
            query = query.filter(cls.created_at <= end_time)

        if email is not None:
            query = query.filter(cls.email == email)
        else:
            query = query.offset(skip).limit(limit)

        return query.all()


class JDO_MODRP_L(Base, BaseMixin):
    """상세모델 동작 이력"""

    __tablename__ = "JDO_MODRP_L"
    __table_args__ = {"extend_existing": True}
    mID = Column(Integer, primary_key=True, nullable=False)
    MODEL_NAME = Column(String(length=45), nullable=True)
    MODEL_VER = Column(String(length=45), nullable=True)
    MODEL_DIR = Column(String(length=45), nullable=True)
    MODEL_SIZE = Column(String(length=45), nullable=True, default="inactive")
    LOG_DIR = Column(String(length=100), nullable=True, default=True)
    MODEL_TYPE = Column(
        Enum(ModelTypeEnum),
        nullable=True,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    SYS_DOC_IMG_SIZE = Column(Integer, nullable=True)
    SERVICE_NAME = Column(Integer, nullable=True)
    RECOG_YN = Column(Integer, nullable=True)
    OUTPUT_DIM = Column(JSON, nullable=True)
    PROPERTY = Column(JSON, nullable=True)


class JDO_MNQLT_H(Base, BaseMixin):
    """최소 퀄리티 검증 이력"""

    __tablename__ = "JDO_MNQLT_H"
    __table_args__ = {"extend_existing": True}
    qID = Column(String(length=100), primary_key=True, nullable=False)
    EDMS_ID = Column(BigInteger, nullable=True)
    mID = Column(String(length=45), ForeignKey("JDO_MODRP_L.mID"), nullable=True)
    START_DTTM = Column(String(length=45), nullable=True)
    END_DTTM = Column(DATETIME, nullable=True)
    TIME = Column(DATETIME, nullable=True)
    LOG_DIR = Column(
        String(length=100),
        nullable=False,
    )
    DOC_IMG_SIZE = Column(String(length=100), nullable=True)
    SCAN_YN = Column(String(length=45), nullable=True)
    RESULT_LOGIT = Column(JSON, nullable=True)
    RESULT_CLS = Column(Enum(ResultClsEnum), nullable=True)


class JDO_OCRSY_H(Base, BaseMixin):
    """OCR 인식 시스템 동작 이력"""

    __tablename__ = "JDO_OCRSY_H"
    __table_args__ = {"extend_existing": True}
    SYS_REL_ID = Column(Integer, primary_key=True, nullable=False)
    qID = Column(String(length=100), ForeignKey("JDO_MNQLT_H.qID"), nullable=True)
    EDMS_ID = Column(String(length=45), ForeignKey("JDO_MNQLT_H.EDMS_ID"), nullable=True)
    START_DTTM = Column(DateTime, nullable=True, default="inactive")
    END_DTTM = Column(DateTime, nullable=True, default=True)
    TIME = Column(
        Time,
        nullable=True,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    LOG_DIR = Column(String(length=100), nullable=True)
    SYS_DOC_IMG_SIZE = Column(String(length=100), nullable=True)
    SERVICE_NAME = Column(String(length=100), nullable=True)
    RECOG_YN = Column(Enum(ReCogYnEnum), nullable=True)
    ERROR_CODE = Column(Enum(ErrorCodeEnum), nullable=True)


class JDO_MODRP_H(Base, BaseMixin):
    """상세모델 동작 이력"""

    __tablename__ = "JDO_MODRP_H"
    __table_args__ = {"extend_existing": True}
    OPER_ID = Column(Integer, primary_key=True, nullable=False)
    SYS_REL_ID = Column(Integer, ForeignKey("JDO_OCRSY_H.SYS_REL_ID"), nullable=True)
    EDMS_ID = Column(String(length=45), ForeignKey("JDO_OCRSY_H.EDMS_ID"), nullable=True)
    mID = Column(Integer, ForeignKey("JDO_MODRP_L.mID"), nullable=True)
    SERVICE_NAME = Column(String(length=100), nullable=True, default="inactive")
    END_DTTM = Column(DateTime, nullable=True, default=True)
    ELAB_TIME = Column(
        Time,
        nullable=True,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    LOG_DIR = Column(String(length=100), nullable=True)
    RECOG_YN = Column(Enum(ReCogYnEnum), nullable=True)
    ERROR_CODE = Column(Enum(ErrorCodeEnum), nullable=True)


class JDO_KEYVA_H(Base, BaseMixin):
    """인식키밸류값 이력"""

    __tablename__ = "JDO_KEYVA_H"
    __table_args__ = {"extend_existing": True}
    OBJ_ID = Column(Integer, primary_key=True, nullable=False)
    OPER_ID = Column(Integer, ForeignKey("JDO_MODRP_H.OPER_ID"), nullable=True)
    EDMS_ID = Column(String(length=45), ForeignKey("JDO_MODRP_H.EDMS_ID"), nullable=True)
    SERVICE_NAME = Column(String(length=100), nullable=True)
    SAVE_TIME = Column(DateTime, nullable=True, default="inactive")
    LOG_DIR = Column(String(length=100), nullable=True, default=True)
    RECOG_YN = Column(
        Enum(ReCogYnEnum),
        nullable=True,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    ERROR_CODE = Column(Enum(ErrorCodeEnum), nullable=True)
    RECOG_KEY = Column(String(length=200), nullable=True)
    RECOG_VALUE = Column(String(length=200), nullable=True)


def create_db_table() -> None:
    # Base.metadata = db
    # Base.metadata.create_all()
    # session = next(db.session())
    # session.create_all()
    # session.commit()
    # session.close()
    Base.metadata.create_all(db._engine)
