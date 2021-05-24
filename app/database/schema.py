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
from database.connection import Base, db


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
    def create(cls, session: Session, auto_commit=False, **kwargs):
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

    # @classmethod 
    # def create_request_quantity(cls, session: Session, auto_commit=False, **kwargs):
    #     obj = cls()
    #     user = session.query(obj).filter(obj.name == kwargs.get("email")).first()
    #     user.inference_request_quantity += 1
    #     for col in obj.all_columns():
    #         col_name = col.name
    #         if col_name in kwargs:
    #             setattr(obj, col_name, kwargs.get(col_name))
    #     session.add(obj)
    #     session.flush()
    #     if auto_commit:
    #         session.commit()
    #     return obj

    @classmethod 
    def test(cls, session: Session, auto_commit=False, **kwargs):
        ...


class Users(Base, BaseMixin):
    __tablename__ = "users"
    username = Column(String(length=128), nullable=True)
    email = Column(String(length=255), nullable=True)
    hashed_password = Column(String(length=2000), nullable=True)
    full_name = Column(String(length=128), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Errors(Base, BaseMixin):
    __tablename__ = "errors"
    url = Column(String(length=2000), nullable=True)
    method = Column(String(length=255), nullable=True)
    status_code = Column(String(length=255), nullable=True)
    error_detail = Column(String(length=2000), nullable=True)
    client = Column(String(length=2000), nullable=True)
    processed_time = Column(String(length=255), nullable=True)
    datetime_kr = Column(String(length=255), nullable=True)


class Logs(Base, BaseMixin):
    __tablename__ = "logs"
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
    # choose email or id ??
    email = Column(String(length=255), nullable=True)
    status_code = Column(Integer, nullable=True)