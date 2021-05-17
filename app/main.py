import uvicorn
import os
import time

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from os import path, environ
from dataclasses import asdict, dataclass
from dotenv import load_dotenv

from routes import auth, index, users, inference
from database.connection import db
from middlewares.token_validator import access_control




POSTGRES_IP_ADDR = os.getenv('POSTGRES_IP_ADDR')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')


# API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)
base_dir = path.dirname(path.dirname(path.abspath(__file__)))
env_path=path.join('/workspace', '.env')

@dataclass
class Config:
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = False
    TEST_MODE: bool = False
    DB_URL: str = environ.get("DB_URL", f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_IP_ADDR}/{POSTGRES_DB}")


load_dotenv(env_path)

app = FastAPI()
db.init_app(app, **asdict(Config()))

app.add_middleware(middleware_class=BaseHTTPMiddleware, dispatch=access_control)

app.include_router(index.router)
app.include_router(inference.router, tags=["inference"])
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

   

# async def create_app():
#     await load_dotenv(env_path)

#     app = FastAPI()
#     db.init_app(app, **asdict(Config()))

#     app.add_middleware(middleware_class=BaseHTTPMiddleware, dispatch=access_control)

#     app.include_router(index.router)
#     app.include_router(inference.router, tags=["inference"])
#     app.include_router(users.router, tags=["Users"], prefix="/users")
#     app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


# app = create_app()