from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, Body
from app.common.const import get_settings
from app.database.connection import db
from app.database import query
from app import models
from app.utils.logging import logger
from app.database.schema import Dataset, Image, Model, Visualize, Category, Task
from sqlalchemy.orm import Session

settings = get_settings()
router = APIRouter()


@router.get("/select/image")
def select_image(image_id: str, db: Session = Depends(db.session)) -> Optional[Image]:
    return query.select_image(db, image_id=image_id)


@router.get("/select/category")
def select_category(dataset_pkey: str, db: Session = Depends(db.session)):
    return query.select_category(db, dataset_pkey=dataset_pkey)


@router.get("/select/dataset")
def select_dataset(dataset_id: str, db: Session = Depends(db.session)) -> List[Dataset]:
    return query.select_dataset(db, dataset_id=dataset_id)


@router.get("/select/category/key")
def select_category_pkey_by_name(
    category_name: str, db: Session = Depends(db.session)
) -> Optional[int]:
    return query.select_category_by_name(db, category_name=category_name)


@router.post("/insert/inference")
def insert_inference_result(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> bool:
    logger.info(data)
    return query.insert_inference_result(db, **data)


@router.post("/create/image")
def insert_image(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> Optional[Image]:
    logger.info(f"create image data: {data}")
    return Image.create(db, **data)


@router.patch("/update/image")
def update_image(
    data: models.UpdateImage = Body(...), db: Session = Depends(db.session)
) -> Optional[Image]:
    logger.info(f"update image data: {data}")
    _id = data.id
    return Image.update(db, id=_id, **data.dict())


@router.post("/create/dataset")
def insert_dataset(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> Optional[Dataset]:
    logger.info(f"create dataset data: {data}")
    return Dataset.create(db, **data)


@router.post("/create/model")
def insert_model(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> Optional[Model]:
    logger.info(f"create model data: {data}")
    return Model.create(db, **data)


@router.post("/create/visualize")
def insert_visualize(
    data: Dict = Body(...), db: Session = Depends(db.session)
) -> Optional[Visualize]:
    logger.info(f"create visualize data: {data}")
    return Visualize.create(db, **data)


@router.get("/select/category_pkey")
def select_category_pkey(
    dataset_id: str, db: Session = Depends(db.session)
) -> List[Category]:
    return query.select_category_pkey(db, dataset_id=dataset_id)


@router.get("/select/category/all")
def select_category_all(db: Session = Depends(db.session)) -> List[Category]:
    return query.select_category_all(db)


@router.post("/create/task")
def create_task(
    params: models.CreateTask = Body(...), db: Session = Depends(db.session)
) -> Optional[Task]:
    return query.insert_task(db, **params)


# @router.post("/create/inference")
# def create_inference(
#     params: models.CreateInference = Body(...),
#     db: Session = Depends(db.session)
# ):
#     return query.insert_inference(db, data=params)
