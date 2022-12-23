
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from rich.console import Console

from app.common.const import get_settings
from app.database.connection import db
from app.service.dataset import (
    upload_cls_training_dataset as upload_cls_training_dataset_service,
    get_cls_train_dataset as get_cls_train_dataset_service,
    delete_cls_train_dataset as delete_cls_train_dataset_service
)
from sqlalchemy.orm import Session


console = Console()
settings = get_settings()
router = APIRouter()




@router.post("/cls")
def upload_cls_training_dataset(
    inputs: dict = Body(...), 
    session: Session = Depends(db.session)
) -> JSONResponse:
    return upload_cls_training_dataset_service(
        inputs = inputs,
        session = session
    )


@router.get("/cls")
def get_cls_train_dataset(
    dataset_id: str, 
    session: Session = Depends(db.session)
) -> JSONResponse:
    return get_cls_train_dataset_service(
        dataset_id = dataset_id,
        session = session
    )


@router.delete("/cls")
def delete_cls_train_dataset(
    dataset_id: str, 
    session: Session = Depends(db.session)
) -> JSONResponse:
    return delete_cls_train_dataset_service(
        dataset_id = dataset_id,
        session = session
    )