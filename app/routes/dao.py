from typing import Dict
from fastapi import APIRouter, Depends, Body
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from app.utils.logging import logger
from app.database.schema import Image, Dataset, Model, Inference, Visualize
from sqlalchemy.orm import Session

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
def insert_inference_result(data: Dict = Body(...), db: Session = Depends(db.session)):
    logger.info(data)
    return query.insert_inference_result(db, **data)

@router.post("/create/image")
def insert_image(data: Dict = Body(...),  db: Session = Depends(db.session)):
    logger.info(f"create image data: {data}")
    return Image.create(db, **data)

@router.post("/create/dataset")
def insert_dataset(data: Dict = Body(...),  db: Session = Depends(db.session)):
    logger.info(f"create dataset data: {data}")
    return Dataset.create(db, **data)

@router.post("/create/model")
def insert_model(data: Dict = Body(...),  db: Session = Depends(db.session)):
    logger.info(f"create model data: {data}")
    return Model.create(db, **data)

@router.post("/create/visualize")
def insert_visualize(data: Dict = Body(...),  db: Session = Depends(db.session)):
    logger.info(f"create visualize data: {data}")
    return Visualize.create(db, **data)

@router.post("/insert/inference_img_path")
def insert_img_path(data: Dict = Body(...),  db: Session = Depends(db.session)):
    logger.info(f"insert infernece_img_path: {data}")
    return Inference.update(session=db, obj_in=data)

@router.get("/select/category_pkey")
def select_category_pkey(dataset_id: str,  db: Session = Depends(db.session)):
    return query.select_category_pkey(db, dataset_id = dataset_id)


# @router.get("/select/inference_image")
# def select_inference_image(task_id: str,  db: Session = Depends(db.session)):
#     return query.select_inference_image(db, task_id = task_id)