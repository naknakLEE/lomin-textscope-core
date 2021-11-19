from fastapi import APIRouter, Depends
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from sqlalchemy.orm import Session
import json

settings = get_settings()
router = APIRouter()

@router.get("/select/image")
def select_image(image_id: str, db: Session = Depends(db.session)):
    return query.select_image(db, image_id = image_id)

@router.get("/select/dataset")
def select_dataset(dataset_id: str, db: Session = Depends(db.session)):
    return query.select_dataset(db, dataset_id = dataset_id)

@router.get("/select/category")
def select_category(model_id: str, db: Session = Depends(db.session)):
    return query.select_category(db, model_id = model_id)


@router.post("/insert/inference")
def insert_inference_result(params: dict, db: Session = Depends(db.session)):
    print(params)
    return query.insert_inference_result(db, **params)


