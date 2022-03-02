import base64
import zipfile
import uuid
import shutil

from minio import Minio
from typing import List
from pathlib import Path
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from rich.console import Console
from rich.progress import track

from app.errors import exceptions as ex
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import db
from app.utils.utils import (
    dir_structure_validation,
    image_file_validation,
)
from app.database import query


console = Console()
settings = get_settings()
router = APIRouter()
mc = Minio(
    f"{settings.MINIO_IP_ADDR}:{settings.MINIO_PORT}",
    secure=False,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    region=settings.MINIO_REGION,
)


def extract_zip_file(object_name, zip_file_path: Path, save_path: Path):
    with console.status("Save zip file..."):
        mc.fget_object("datasets", object_name, zip_file_path.as_posix())
    
    with console.status("Extract zip file..."):
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_file:
                zip_file.extractall(save_path)
        except Exception as exc:
            msg = "Zip file validation"
            logger.exception(msg)
            raise HTTPException(status_code=415, detail=vars(ex.ExtractException(msg=msg, exc=str(exc))))


def check_dataset_validation(dataset_path, image_paths):
    validation_result = dir_structure_validation(dataset_path)
    if not validation_result:
        raise HTTPException(status_code=415, detail=vars(ex.ValidationFailedException(msg="Directory structure validation failed")))

    for image_path in track(image_paths, description="Image file validation..."):
        is_valid_file = image_file_validation(image_path)
        if not is_valid_file:
            logger.error(f"Invalid image: {image_path.name}")
        if not is_valid_file:
            raise HTTPException(status_code=415, detail=vars(ex.ValidationFailedException(msg="file validation failed")))


# TODO: 한 부분이라도 실패하면 전체 롤백하도록 트랜잭션 구성
def insert_dataset_related_data(
    session: Session, 
    dataset_id: str, 
    dataset_path: Path, 
    dataset_dir_name: str, 
    image_paths: List[Path]
):
    with console.status("Inserting dataset..."):
        result = query.insert_training_dataset(
            session=session,
            dataset_id=dataset_id,
            root_path=dataset_path.as_posix(),
            dataset_dir_name=dataset_dir_name,
        )
        if isinstance(result, str):
            return JSONResponse(status_code=302, content=vars(ex.AlreadyExistDataException(target=result)))
        dataset_pkey, dataset_id = result.dataset_pkey, result.dataset_id
    
    saved_dataset_dir = dataset_path / "train"
    new_categories = list(saved_dataset_dir.iterdir())
    for category in track(new_categories, description="Inserting category info..."):
        category_pkey = query.insert_category(
            session=session,
            category_name_en=category.name,
            category_name_kr=category.name,
            category_code=category.name,
            dataset_pkey=dataset_pkey    
        )

    for image_path in track(image_paths, description="Inserting image info..."):
        query.insert_image(
            session=session,
            image_id=str(uuid.uuid4()),
            image_path=str(image_path),
            category_pkey=category_pkey,
            dataset_pkey=dataset_pkey,
            image_type="TRAINING",    
        )


@router.post("/cls")
def upload_cls_training_dataset(
    inputs: dict = Body(...), session: Session = Depends(db.session)
) -> JSONResponse:
    dataset_id = inputs.get("dataset_id")
    object_name = inputs.get("object_name", "")

    dataset_dir_name = Path(object_name).stem
    save_path = Path(settings.ZIP_PATH) / dataset_dir_name / dataset_id
    is_exist = save_path.exists()
    if is_exist:
        raise HTTPException(
            status_code=415, 
            detail=vars(ex.NotExistException(msg="This dataset already exists"))
        )
    save_path.mkdir(exist_ok=True, parents=True)

    zip_file_path = save_path / object_name
    dataset_path = save_path / dataset_dir_name
    logger.info("Zip file path: {}".format(zip_file_path.as_posix()))
    logger.info("Save path: {}".format(save_path.as_posix()))

    with console.status("Glob image paths..."):
        image_paths = list(dataset_path.rglob('*.*'))

    extract_zip_file(object_name, zip_file_path, save_path)
    
    check_dataset_validation(dataset_path, image_paths)

    insert_dataset_related_data(session, dataset_id, dataset_path, dataset_dir_name, image_paths)

    response_log = dict(
        is_exist=is_exist,
        image_list=image_paths,
    )
    return JSONResponse(
        status_code=200, 
        content=jsonable_encoder({ "response_log": response_log })
    )


@router.get("/cls")
def get_cls_train_dataset(
    dataset_id: str, session: Session = Depends(db.session)
) -> JSONResponse:
    # TODO: API 문서에 명시된 형식대로 리턴하도록 구성
    dataset = query.select_dataset(session, dataset_id=dataset_id)
    categories = query.select_category(session, dataset_pkey=dataset.dataset_pkey)
    return JSONResponse(status_code=200, content=jsonable_encoder(dict(
            categories=categories,
            dataset=dataset,
        )))


@router.delete("/cls")
def delete_cls_train_dataset(
    dataset_id: str, session: Session = Depends(db.session)
) -> JSONResponse:
    target_dataset = query.select_dataset(session, dataset_id=dataset_id)

    target_path = Path(target_dataset.root_path)
    is_exist = target_path.exists()
    if is_exist:
        shutil.rmtree(target_path.parent, ignore_errors=True)

    query.delete_category_cascade_image(
        session=session, 
        dataset_pkey=target_dataset.dataset_pkey
    )
    query.delete_dataset(session, dataset_id)
    mc.remove_object("datasets", target_path.name + ".zip")
    return PlainTextResponse(content="\n", status_code=200)