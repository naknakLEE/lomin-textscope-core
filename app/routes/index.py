from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.responses import Response
from inspect import currentframe as frame

from database.connection import db
from database.schema import Users, Errors
from common.const import FAKE_INFORMATION




router = APIRouter()


@router.get("/")
async def index():
    # user = Users(status='active')
    # session.add(user)
    # session.commit()

    # Errors.create(next(db.session()), auto_commit=True)
    # Users.create(session, auto_commit=True, name="test", **FAKE_INFORMATION)

    curren_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {curren_time.strftime('%Y.%m.%d %H:%M:%S')})")


@router.get("/test")
async def test(request: Request):
    print("state.user", request.state.user)
    # await index()
    # Errors.create(next(db.session()), auto_commit=True)
    # Users.create(session, auto_commit=True, name="test", **FAKE_INFORMATION)
    try:
        a = 1/0
    except Exception as e:
        request.state.inspect = frame()
        raise e
    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")


@router.get("/status")
def check_status():
    # return JSONResponse(status_code=200, content=f"{[postgresConnection][0]}")
    return JSONResponse(status_code=200, content=f"postgresConnection")