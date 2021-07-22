import uvicorn
import os

from fastapi import FastAPI, Request, Depends
from fastapi import Depends, File, UploadFile, APIRouter

from pp_server.app.routes import document


def app_generator() -> FastAPI:
    app = FastAPI()
    app.include_router(document.router, tags=["Document"], prefix="/post_processing")
    return app
