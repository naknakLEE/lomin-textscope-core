import enum

from typing import List
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
    Enum,
    ForeignKey,
)
from sqlalchemy.sql.sqltypes import BIGINT

from kb_wrapper.app.database.connection import Base, db


class StatusEnum(enum.Enum):
    active = 1
    inactive = 2
    disabled = 3


class ResultClsEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D53 = 3
    D54 = 4


class ReCogYnEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D53 = 3
    D54 = 4


class ErrorCodeEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D53 = 3
    D54 = 4


class ModelTypeEnum(enum.Enum):
    D01 = 1
    D02 = 2
    D53 = 3
    D54 = 4


class BaseMixin:
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"
        ]


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
    qID = Column(BIGINT, ForeignKey("JDO_MNQLT_H.qID"), nullable=True)
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
    Base.metadata.create_all(db._engine)
