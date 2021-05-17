import psycopg2
import os
import requests
import numpy as np 
import cv2
import uvicorn

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from dotenv import load_dotenv




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
cursor = postgresConnection.cursor()

username = 'shinuk'
cursor.execute(f"SELECT * FROM {TABLE} WHERE username = '{username}'")

row = cursor.fetchone()
fake_information = {
    "shinuk": {
        "username": row[1],
        "full_name": row[2],
        "email": row[3],
        "hashed_password": row[4],
        "disabled": row[5],
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(debug=True)

log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        cursor.execute(f"SELECT * FROM {TABLE} WHERE username = '{username}'")
        row = cursor.fetchone()
        user_dict = {
            "username": row[1],
            "full_name": row[2],
            "email": row[3],
            "disabled": row[4],
            "hashed_password": row[5],
        }
        # user_dict = db[username]
        print("check", type(user_dict), user_dict)
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    # print("check", type(user), user)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_information, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



@router.post("/inference") 
def inference(current_user: User = Depends(get_current_active_user), file: UploadFile = File(...)):
    test_url = f'http://{SERVING_IP_ADDR}:{SERVING_IP_PORT}/inference'

    image_data = file.file.read()
    nparr = np.fromstring(image_data, np.uint8)
    image_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    _, img_encoded = cv2.imencode('.jpg', image_data)
    image_data = img_encoded.tobytes()

    files = { 'file': image_data }
    response = requests.post(test_url, data=image_data)

    return response.json()