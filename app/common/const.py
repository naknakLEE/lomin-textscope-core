POSTGRES_IP_ADDR="182.20.0.6"
WEB_IP_ADDR="182.20.0.5"
SERVING_IP_ADDR="182.20.0.4"

POSTGRES_DB="shinuk"
POSTGRES_USER="shinuk"
POSTGRES_PASSWORD="1q2w3e4r"

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = "30"

TABLE="users"

SERVING_IP_PORT='5000'

EXCEPT_PATH_LIST=["/", "/openapi.json"]
EXCEPT_PATH_REGEX="^(/docs|/redoc|/api/auth)"

FAKE_INFORMATION={
    "username": "shinuk",
    "full_name": "Shinuk Yi",
    "email": "shinuk@example.com",
    "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
}

FILE_MAX_BYTE=1024*1024
BACKUP_COUNT=100000000

LOGGER_LEVEL="DEBUG"