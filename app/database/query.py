import json
import uuid
from fastapi import HTTPException
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app import models
from app.database import schema
from app.utils.logging import logger
from app.database.connection import Base


def create_db_table(db: Session) -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
    finally:
        session.close()


def insert_initial_data(db: Session) -> None:
    try:
        session = next(db.session())
        with open("/workspace/assets/heungkuklife.json", "r") as f:
            json_database_initial_data = json.load(f)
        database_initial_data = json_database_initial_data["DATABASE_INITIAL_DATA"]
        for object_table in Base.metadata.sorted_tables:
            table_initial_data = database_initial_data[object_table.name]
            if len(table_initial_data) == 0:
                continue
            if (
                db._engine.execute(f"SELECT count(*) FROM {object_table.name}").scalar()
                == 0
            ):
                db._engine.execute(object_table.insert(), table_initial_data)
    except Exception:
        logger.exception("insert error")
    finally:
        session.close()


### image
def select_image_by_pkey(db: Session, image_pkey: int) -> schema.Image:
    query = (
        db.query(schema.Image)
        .select_from(schema.Image)
        .filter(schema.Image.image_pkey == image_pkey)
    )
    res = query.first()
    return res


def select_image_all(db: Session) -> Optional[List[schema.Image]]:
    """
    SELECT
        *
    FROM
        image
    """
    dao = schema.Image
    try:
        res = dao.get_all(db)
    except Exception:
        logger.exception("image select error")
        res = None
    return res


def select_image(db: Session, **kwargs: Dict) -> Optional[schema.Image]:
    dao = schema.Image
    try:
        res = dao.get(db, **kwargs)
    except Exception:
        logger.exception("image select error")
        res = None
    return res


def insert_image(
    session: Session,
    image_path: str,
    category_pkey: Optional[int] = None,
    dataset_pkey: Optional[int] = None,
    image_id: str = str(uuid.uuid4()),
    image_type: str = "TRAINING",
) -> Optional[schema.Image]:
    dao = schema.Image
    try:
        result = dao.create(
            session=session,
            image_path=image_path,
            category_pkey=category_pkey,
            dataset_pkey=dataset_pkey,
            image_id=image_id,
            image_type=image_type,
        )
    except Exception as e:
        logger.error(f"image insert error: {e}")
        session.rollback()
        return None
    return result


### category
def select_category(db: Session, **kwargs: Dict) -> Optional[schema.Category]:
    dao = schema.Category
    try:
        res = dao.get_all(db, **kwargs)
    except Exception as e:
        logger.exception(f"category select error: {e}")
        res = None
    return res


def update_task(
    db: Session, pkey: int, data: models.UpdateTask
) -> Optional[schema.Task]:
    dao = schema.Task
    try:
        result = dao.update(db, pkey=pkey, **data.dict())
    except Exception as e:
        logger.error(f"task update error: {e}")
        db.rollback()
        result = None
    return result


### inference
def insert_inference(
    db: Session, data: models.CreateInference
) -> Optional[schema.Inference]:
    dao = schema.Inference
    try:
        result = dao.create(db, **data.dict())
    except Exception as e:
        logger.error(f"inference insert error: {e}")
        db.rollback()
        result = None
    return result


def select_inference_by_type(
    db: Session, inference_type: str
) -> List[schema.Inference]:
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.inference_type == inference_type)
    )
    res = query.all()
    return res


def select_dataset(db: Session, dataset_id: str) -> List[schema.Dataset]:
    """
    SELECT
        *
    FROM
        dataset
    WHERE
        dataset_id = 'ttt-ttt-ttt-ttt'
    """

    query = (
        db.query(schema.Dataset)
        .select_from(schema.Dataset)
        .filter(schema.Dataset.dataset_id == dataset_id)
    )
    return query.first()


def insert_inference_result(
    session: Session,
    task_pkey: int,
    image_pkey: int,
    inference_type: str,
    response_log: Dict,
    inference_results: Dict,
) -> None:
    del inference_results["response_log"]
    try:
        schema.Inference.create(
            session=session,
            task_pkey=task_pkey,
            image_pkey=image_pkey,
            inference_results=inference_results,
            inference_type=inference_type,
            response_log=response_log,
            start_datetime=response_log.get("inference_start_time"),
            end_datetime=response_log.get("inference_end_time"),
        )
    except Exception:
        logger.exception(f"Insert inference result")


def insert_training_dataset(
    session: Session,
    dataset_id: str,
    root_path: str,
    dataset_dir_name: str,
) -> Optional[schema.Dataset]:
    res = schema.Dataset.create(
        session=session,
        dataset_id=dataset_id,
        root_path=root_path,
        dataset_dir_name=dataset_dir_name,
    )
    return res


def insert_category(
    session: Session,
    category_name: str,
    category_code: str,
    dataset_pkey: int,
) -> int:
    res = schema.Category.create(
        session=session,
        category_name=category_name,
        category_code=category_code,
        dataset_pkey=dataset_pkey,
    )
    return res.category_pkey


def insert_inference_image(db: Session, **kwargs: Dict[str, Any]) -> int:
    res = schema.Image.create(db, **kwargs)
    return res.image_pkey


def select_inference_img_path_from_taskid(
    db: Session, task_id: str
) -> Optional[schema.Visualize]:
    query = (
        db.query(schema.Visualize.inference_img_path)
        .select_from(schema.Visualize)
        .filter(schema.Visualize.task_id == task_id)
    )
    res = query.first()
    return res


def delete_dataset(db: Session, dataset_id: str) -> bool:
    try:
        query = db.query(schema.Dataset).filter_by(dataset_id=dataset_id).delete()
    except Exception:
        logger.exception("dataset delete error")
        db.rollback()
        return False
    logger.info(f"Delete catetory successful")
    return True


def select_inference_all(db: Session) -> List[schema.Inference]:
    query = (
        db.query(schema.Inference, schema.Image, schema.Category)
        .select_from(schema.Inference)
        .join(schema.Image, schema.Image.image_pkey == schema.Inference.image_pkey)
        .join(
            schema.Category, schema.Category.category_pkey == schema.Image.category_pkey
        )
    )

    res = query.all()
    return res


def delete_inference_all(db: Session) -> bool:
    try:
        db.query(schema.Inference).delete()
    except Exception:
        logger.exception("inference delete error")
        db.rollback()
        return False
    return True


def select_category_pkey(db: Session, dataset_id: str) -> List[schema.Category]:
    """
    SELECT
        DISTINCT category_pkey
    FROM
        image
    WHERE
        dataset_pkey IN
            (
                SELECT
                    dataset_pkey
                FROM
                    dataset
                WHERE
                    dataset_id = 'b0839c1c-7099-4743-901c-b4d66e173e97'
            )
    """
    dataset_pkeys = (
        db.query(schema.Dataset.dataset_pkey)
        .select_from(schema.Dataset)
        .filter(schema.Dataset.dataset_id == dataset_id)
        .all()
    )

    category_pkeys = (
        db.query(schema.Image.category_pkey)
        .select_from(schema.Image)
        .filter(schema.Image.dataset_pkey.in_(dataset_pkeys))
        .distinct()
        .all()
    )

    query = (
        db.query(schema.Category)
        .select_from(schema.Category)
        .filter(schema.Category.category_pkey.in_(category_pkeys))
    )  # .filter(schema.Category.is_pretrained == False)

    res_category = query.all()
    return res_category


def select_inference_image(db: Session, task_id: str) -> List[schema.Inference]:
    query = (
        db.query(schema.Inference, schema.Image)
        .select_from(schema.Inference)
        .join(schema.Image, schema.Inference.image_pkey == schema.Image.image_pkey)
        .filter(schema.Inference.task_id == task_id)
    )
    res = query.all()
    return res


def select_gocr_inference_from_taskid(
    db: Session, task_id: str
) -> List[schema.Inference]:
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.task_id == task_id)
        .filter(schema.Inference.inference_type == "gocr")
    )

    res = query.all()
    return res


def select_kv_inference_from_taskid(
    db: Session, task_id: str
) -> Optional[schema.Inference]:
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.task_id == task_id)
        .filter(schema.Inference.inference_type == "kv")
    )

    res = query.first()
    return res


def select_category_all(
    db: Session, **kwargs: Dict[str, Any]
) -> Optional[List[schema.Category]]:
    res = schema.Category.get_all(db, **kwargs)
    return res


def select_category_by_name(db: Session, category_name: str) -> Optional[int]:
    """
    SELECT
        category_pkey
    FROM
        category
    WHERE
        category_name = {category_name}
    """
    query = (
        db.query(schema.Category)
        .select_from(schema.Category)
        .filter(
            or_(
                schema.Category.category_name == category_name,
            )
        )
    )

    res = query.first()
    if res:
        return res.category_pkey
    return None


def select_category_by_pkey(db: Session, category_pkey: int) -> schema.Category:
    """
    SELECT
        *
    FROM
        category
    WHERE
        category_pkey = {category_pkey}
    """
    query = (
        db.query(schema.Category)
        .select_from(schema.Category)
        .filter(schema.Category.category_pkey == category_pkey)
    )

    res = query.first()
    return res


def delete_category_cascade_image(session: Session, dataset_pkey: int) -> bool:
    """
    DELETE FROM
        image
    WHERE
        image.category_pkey = {
            SELECT
                category_pkey
            FROM
                category
            WHERE
                is_pretrained = False
        }
        image.dataset_pkey = {dataset_pkey}

    DELETE FROM
        category
    WHERE
        is_pretrained = False
    """
    query = session.query(schema.Category)

    res = query.all()

    for category in res:
        try:
            q = (
                session.query(schema.Image)
                .filter(and_(schema.Image.category_pkey == category.category_pkey))
                .delete()
            )
        except Exception:
            logger.exception("image cascade delete error")
            session.rollback()
            return False

    try:
        query.delete()
    except Exception:
        logger.exception("category cascade delete error")
        session.rollback()
        return False
    session.commit()
    logger.info(f"Delete catetory successful")
    return True


def insert_task(session: Session, task_id: str, image_pkey: str) -> int:
    if image_pkey is None:
        logger.warning("Image pkey({}) not found".format(image_pkey))
    dao = schema.Task
    result = dao.create(
        session=session, task_id=task_id, task_type="TRAINING", image_pkey=image_pkey
    )
    if result is None:
        logger.warning("{} insert failed, image pkey={}".format(task_id, image_pkey))
        # TODO: 아래 라인 models로 이전
        error = models.Error(
            error_code="ER-INF-CKV-4003", error_message="이미 등록된 task id"
        )
        raise HTTPException(status_code=400, detail=vars(error))
    return result.task_pkey
