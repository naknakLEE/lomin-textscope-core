import uvicorn
import os

from fastapi import FastAPI
from os import path, environ
from dataclasses import asdict, dataclass

from routes import auth, index, users, inference
from database.connection import db

from dotenv import load_dotenv



env_path=path.join('/workspace', '.env')
load_dotenv(env_path)

POSTGRES_IP_ADDR = os.getenv('POSTGRES_IP_ADDR')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')


# API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)
base_dir = path.dirname(path.dirname(path.abspath(__file__)))

@dataclass
class Config:
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = False
    TEST_MODE: bool = False
    DB_URL: str = environ.get("DB_URL", f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_IP_ADDR}/{POSTGRES_DB}")


app = FastAPI()
db.init_app(app, **asdict(Config()))


app.include_router(index.router)
app.include_router(inference.router, tags=["inference"])
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

   