import uvicorn
import os

from fastapi import FastAPI, Request, Depends
from fastapi import Depends, File, UploadFile, APIRouter

from pp_server.app.routes import document, kv


def app_generator() -> FastAPI:
    app = FastAPI()
    app.include_router(kv.router, tags=["KV"], prefix="/post_processing")
    app.include_router(document.router, tags=["Document"], prefix="/post_processing")
    return app
