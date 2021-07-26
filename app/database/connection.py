import logging
import os

from typing import Generator, Any
from fastapi import FastAPI
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy_utils.functions import database_exists, create_database


from app.common.const import get_settings


settings = get_settings()


class SQLAlchemy:
    def __init__(self, app: FastAPI = None, **kwargs) -> None:
        self._engine = None
        self._session = None
        if app is not None:
            self.init_app(app=app, **kwargs)

    def init_app(self, app: FastAPI, **kwargs) -> None:
        database_url = kwargs.get("DB_URL")
        if not database_exists(database_url):
            create_database(database_url)
        pool_recycle = kwargs.setdefault("DB_POOL_RECYCLE", 900)
        echo = kwargs.setdefault("DB_ECHO", False)

        check_same_thread = {}
        if os.environ["API_ENV"] == "test":
            check_same_thread = {"check_same_thread": False}
        self._engine = create_engine(
            database_url,
            connect_args=check_same_thread,
            echo=echo,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
            # pool_size=30,
        )
        self._session = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

        @app.on_event("startup")
        def startup() -> None:
            self._engine.connect()
            logging.info("DB connected.")

        @app.on_event("shutdown")
        def shutdown() -> None:
            self._session.close_all()
            self._engine.dispose()
            logging.info("DB disconnected")

    def get_db(self) -> Generator:
        if self._session is None:
            raise Exception("must be called 'init_app'")
        # db_session = None
        db_session = self._session()
        try:
            yield db_session
        finally:
            db_session.close()

    @property
    def session(self) -> Generator:
        return self.get_db

    @property
    def engine(self) -> Engine:
        return self._engine


db = SQLAlchemy()
Base = declarative_base()
