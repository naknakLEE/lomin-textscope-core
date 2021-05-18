import os
from dotenv import load_dotenv


env_path=os.path.join('/workspace', '.env')
load_dotenv(env_path)


POSTGRES_IP_ADDR=os.getenv("POSTGRES_IP_ADDR")
WEB_IP_ADDR=os.getenv("WEB_IP_ADDR")
SERVING_IP_ADDR=os.getenv("SERVING_IP_ADDR")

POSTGRES_DB=os.getenv("POSTGRES_DB")
POSTGRES_USER=os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

TABLE="users"

SERVING_IP_PORT=int(os.getenv("SERVING_IP_PORT"))

EXCEPT_PATH_LIST=["/", "/openapi.json"]
EXCEPT_PATH_REGEX="^(/docs|/redoc|/api/auth)"

# pasword == 123456
FAKE_INFORMATION={
    "username": "user",
    "full_name": "user",
    "email": "user@example.com",
    "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
}

FILE_MAX_BYTE=1024*1024
BACKUP_COUNT=100000000

LOGGER_LEVEL="DEBUG"