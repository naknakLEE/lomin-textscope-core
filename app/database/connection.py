import logging
import os

from typing import Callable, Dict, Generator
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy_utils.functions import database_exists, create_database


from app.common.const import get_settings


settings = get_settings()


class SQLAlchemy:
    def __init__(self, app: FastAPI = None, **kwargs: Dict):
        self._engine = None
        self._session = None
        if app is not None:
            self.init_app(app=app, **kwargs)

    def init_app(self, app: FastAPI, **kwargs: Dict) -> None:
        database_url = kwargs.get("DB_URL") 
        if not database_exists(database_url):
            create_database(database_url)
        pool_recycle = kwargs.get("DB_POOL_RECYCLE", 900)
        echo = kwargs.get("DB_ECHO", False)
        pool_size = kwargs.get("POOL_SIZE", 30)
        max_overflow = kwargs.get("MAX_OVERFLOW", 60)

        check_same_thread: Dict = {}
        if os.getenv("API_ENV", "production") == "test":
            check_same_thread = {"check_same_thread": False}
        engine_config = dict(
            name_or_url=database_url,
            connect_args=check_same_thread,
            echo=echo,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        if os.getenv("API_ENV", "production") == "test":
            del engine_config["pool_size"], engine_config["max_overflow"]
        self._engine = create_engine(**engine_config)
        self._session = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

        @app.on_event("startup")
        def startup() -> None:
            if self._engine:
                self._engine.connect()
                logging.info("DB connected.")

        @app.on_event("shutdown")
        def shutdown() -> None:
            if self._session:
                self._session.close_all()
            if self._engine:
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
    def session(self) -> Callable:
        return self.get_db

    @property
    def engine(self) -> Engine:
        return self._engine


db = SQLAlchemy()
Base = declarative_base()
