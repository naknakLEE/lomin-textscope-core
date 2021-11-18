from fastapi import APIRouter, Depends
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from sqlalchemy.orm import Session
import json

settings = get_settings()
router = APIRouter()

@router.get("/get_image_path")
def get_image_path(image_id: str, db: Session = Depends(db.session)):
    return query.get_image_path(db, image_id = image_id)

@router.get("/get_root_dir")
def get_root_dir(dataset_id: str, db: Session = Depends(db.session)):
    return query.get_root_dir(db, image_id = dataset_id)

@router.get("/insert_insert_inference_result")
def insert_insert_inference_result(task_id: int, inferenec_result: json, inference_type: str, image_pkey: int, db: Session = Depends(db.session)):
    return query.insert_insert_inference_result(db, task_id = task_id, inferenec_result = inferenec_result, inference_type = inference_type, image_pkey = image_pkey)

