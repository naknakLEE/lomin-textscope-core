

from fastapi import APIRouter
import psycopg2
import os
import requests
import numpy as np 
import cv2
import uvicorn

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from starlette.requests import Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from dotenv import load_dotenv

# from logger import init_logging
# from loguru import logger
# import logging


# init_logging()

router = APIRouter()


env_path=os.path.join('/workspace', '.env')
load_dotenv(env_path)

POSTGRES_IP_ADDR = os.getenv('POSTGRES_IP_ADDR')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

TABLE = os.getenv('TABLE')

SERVING_IP_ADDR = os.getenv('SERVING_IP_ADDR')
SERVING_IP_PORT = os.getenv('SERVING_IP_PORT')

postgresConnection = psycopg2.connect(
    host=POSTGRES_IP_ADDR,
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)



router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/status")
def check_status():
    return JSONResponse(status_code=200, content=f"{[postgresConnection][0]}")
