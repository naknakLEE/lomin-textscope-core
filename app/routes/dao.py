from typing import Dict
from fastapi import APIRouter, Depends, Body
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from app import models
from app.utils.logging import logger
# from app.database.schema import Image, Dataset, Model, Inference, Visualize
from sqlalchemy.orm import Session

settings = get_settings()
router = APIRouter()

@router.get("/select/image")
def select_image(image_id: str, db: Session = Depends(db.session)):
    return query.select_image(db, image_id=image_id)

@router.get("/select/category")
def select_category(category_code: str, db: Session = Depends(db.session)):
    return query.select_category(db, category_code=category_code)

@router.post("/create/task")
def create_task(
    params: models.CreateTask = Body(...),
    db: Session = Depends(db.session)
):
    return query.insert_task(db, data=params)

@router.post("/create/inference")
def create_inference(
    params: models.CreateInference = Body(...),
    db: Session = Depends(db.session)
):
    return query.insert_inference(db, data=params)