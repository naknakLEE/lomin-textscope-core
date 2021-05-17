from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.responses import Response

from database.connection import db
from database.schema import Users, Errors



router = APIRouter()


fake_information = {
    "username": "shinuk",
    "full_name": "Shinuk Yi",
    "email": "shinuk@example.com",
    "hashed_password": "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
}

@router.get("/")
async def index(session: Session = Depends(db.session)):
    # user = Users(status='active')
    # session.add(user)
    # session.commit()

    # Errors.create(session, auto_commit=True)
    Users.create(session, auto_commit=True, name="test", **fake_information)

    curren_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {curren_time.strftime('%Y.%m.%d %H:%M:%S')})")



@router.get("/status")
def check_status():
    # return JSONResponse(status_code=200, content=f"{[postgresConnection][0]}")
    return JSONResponse(status_code=200, content=f"postgresConnection")
