import base64
import zipfile
import os
import uuid

from typing import Dict, List
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from sqlalchemy.orm import Session
from app.utils.utils import (
    cal_time_elapsed_seconds,
    dir_structure_validation,
    image_file_validation,
)
from app.database import query


settings = get_settings()
router = APIRouter()


@router.post("/cls")
def upload_cls_training_dataset(
    request: dict = Body(...), session: Session = Depends(db.session)
) -> JSONResponse:
    inputs = request
    response = dict()
    request_datetime = datetime.now()
    response_log = dict()
    encoded_file = inputs.get("file", "")
    decoded_file = base64.b64decode(encoded_file)
    file_name = inputs.get("file_name", "")
    save_path = Path(settings.ZIP_PATH) / file_name

    Path(settings.ZIP_PATH).mkdir(exist_ok=True)

    with save_path.open("wb") as file:
        file.write(decoded_file)

    # zip file validation
    try:
        with zipfile.ZipFile(save_path, "r") as zip_file:
            zip_file.extractall(save_path.parent)
    except Exception as ex:
        response = dict(
            request_datetime=request_datetime,
            response_datetime=datetime.now(),
            message=f"zip file validation failed: {ex}",
        )
        logger.warning(response.get("msg"))
        return JSONResponse(status_code=415, content=jsonable_encoder(response))

    zip_file_name = Path(file_name).stem
    zip_folder_path = save_path.parent / zip_file_name
    is_exist = zip_folder_path.exists()
    if not is_exist:
        response = dict(
            request_datetime=request_datetime,
            response_datetime=datetime.now(),
            message=f"zip extraction failed",
        )
        logger.warning(response.get("msg"))
        return JSONResponse(status_code=415, content=jsonable_encoder(response))

    # category validation
    category_dirs = list(zip_folder_path.iterdir())
    is_category_dirs = [d.is_dir() for d in category_dirs]
    if not all(is_category_dirs):
        response = dict(
            request_datetime=request_datetime,
            response_datetime=datetime.now(),
            message=f"category directory validation failed",
        )
        logger.warning(response.get("msg"))
        return JSONResponse(status_code=415, content=jsonable_encoder(response))

    # sub directory validation
    validation_result = dir_structure_validation(zip_folder_path)
    if not validation_result:
        response = dict(
            request_datetime=request_datetime,
            response_datetime=datetime.now(),
            message=f"directory structure validation failed",
        )
        logger.warning(response.get("msg"))
        return JSONResponse(status_code=415, content=jsonable_encoder(response))

    # image validation
    images = list(set(zip_folder_path.rglob("*")) - set(category_dirs))
    for image in images:
        file_validation_result = image_file_validation(image)
        logger.info(f"file validation: {zip_file_name}, {file_validation_result}")
        if file_validation_result:
            response = dict(
                request_datetime=request_datetime,
                response_datetime=datetime.now(),
                message=f"file validation failed",
            )
            logger.warning(response.get("msg"))
            return JSONResponse(status_code=415, content=jsonable_encoder(response))

    dao_dataset_params = {
        "dataset_id": inputs.get("dataset_id"),
        "root_path": str(zip_folder_path),
        "zip_file_name": zip_file_name,
    }
    dataset_pkey, dataset_id = query.insert_training_dataset(
        session, kwargs=dao_dataset_params
    )
    new_categories = list(save_path.parent.joinpath(zip_file_name).iterdir())
    support_set_path = Path(settings.SUPPORT_SET_DIR)
    pretrained_categories = [d for d in support_set_path.iterdir() if d.is_dir()]

    exist_category_list = query.select_category_all(session)
    exist_category_name_list: List[str] = list()
    for category in exist_category_list:
        if category:
            exist_category_name_list.append(category.category_name_en)

    check_category_else_flag = False
    for exist_category in exist_category_list:
        if exist_category.category_name_en == "기타":
            check_category_else_flag = True

    if not check_category_else_flag:
        dao_category_params = {
            "category_name_en": "기타",
            "category_code": "P01",
            "is_pretrained": True,
        }
        query.insert_category(session, kwargs=dao_category_params)

    if not exist_category_list:
        for pre_trained_category in pretrained_categories:
            dao_category_params = {
                "category_name_en": pre_trained_category.name,
                "category_code": "P01",
                "is_pretrained": True,
            }
            category_pkey = query.insert_category(session, kwargs=dao_category_params)

    for category in new_categories:
        if category.name not in exist_category_name_list:
            dao_category_params = {
                "category_name_en": category.name,
                "category_code": "A01",
                "is_pretrained": False,
            }
            category_pkey = query.insert_category(session, kwargs=dao_category_params)
        else:
            category_pkey = query.select_category_by_name(
                session, category_name=category.name
            )

        for image in images:
            if str(image).find(category.name) != -1:
                dao_image_params = {
                    "image_id": str(uuid.uuid4()),
                    "image_path": str(image),
                    "category_pkey": category_pkey,
                    "dataset_pkey": dataset_pkey,
                    "image_type": "training",
                }
                query.insert_image(session, kwargs=dao_image_params)

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
            is_exist=is_exist,
            image_list=images,
        )
    )

    response.update(dict(response_log=response_log))

    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.get("/cls")
def get_cls_train_dataset(
    dataset_id: str, session: Session = Depends(db.session)
) -> JSONResponse:
    response = dict()
    request_datetime = datetime.now()
    response_log = dict()

    dao_object = query.select_dataset(session, dataset_id=dataset_id)
    dataset = [do.dict() for do in dao_object]

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            dataset=dataset,
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )
    response.update(dict(dataset=dataset, response_log=response_log))

    return JSONResponse(status_code=200, content=jsonable_encoder(response))


@router.delete("/cls")
def delete_cls_train_dataset(
    dataset_id: str, session: Session = Depends(db.session)
) -> JSONResponse:
    response: Dict = dict()
    request_datetime = datetime.now()
    response_log: Dict = dict()

    target_dataset = query.select_dataset(session, dataset_id=dataset_id)[0]

    target_path = Path(target_dataset.root_path)

    is_exist = target_path.exists()
    images = list()
    if is_exist:
        images = list(target_path.glob("**/*.*"))
        dirs = [d for d in target_path.iterdir() if d.is_dir()]
        response_log.update(dict(images=[], dirs=[]))
        for image in images:
            response_log["images"].append(str(image))
            try:
                os.remove(image)
            except:
                # @TODO: not exists file exception
                pass
        for d in dirs:
            response_log["dirs"].append(str(d))
            try:
                d.rmdir()
            except:
                # @TODO: directory not empty or directory not exists
                pass
        # remove root path
        target_path.rmdir()
    else:
        # @TODO: target dataset directory가 없을 경우에 대한 exception raise
        pass

    query_result = query.delete_category_cascade_image(
        session, dataset_pkey=target_dataset.dataset_pkey
    )
    query.delete_dataset(session, dataset_id)

    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    response_log.update(
        dict(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            elapsed=elapsed,
        )
    )

    response.update(dict(response_log=response_log))

    return JSONResponse(status_code=200, content=jsonable_encoder(response))
