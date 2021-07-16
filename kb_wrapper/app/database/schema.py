import enum

from typing import List, TypeVar, Optional
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
from sqlalchemy.orm import Session

from kb_wrapper.app.database.connection import Base, db

ModelType = TypeVar("ModelType", bound=Base)


class BaseMixin:
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def all_columns(self) -> List:
        return [
            c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"
        ]


class Logs(Base, BaseMixin):
    __tablename__ = "logs"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    url = Column(String(length=2000), nullable=False)
    method = Column(String(length=255), nullable=False)
    status_code = Column(String(length=255), nullable=False)
    log_detail = Column(String(length=2000), nullable=True)
    error_detail = Column(JSON, nullable=True)
    client = Column(String(length=2000), nullable=True)
    request_timestamp = Column(String(length=255), nullable=False)
    response_timestamp = Column(String(length=255), nullable=False)
    processed_time = Column(String(length=255), nullable=False)

    @classmethod
    def create_log(cls, session: Session, auto_commit=True, **kwargs) -> Optional[ModelType]:
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


def create_db_table() -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
    finally:
        session.close()
