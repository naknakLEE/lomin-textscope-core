import json
from typing import Dict, List, Optional, Tuple, Union
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


def insert_image(db: Session, **kwargs: Dict) -> Optional[schema.Image]:
    dao = schema.Image
    try:
        result = dao.create(db, **kwargs)
    except Exception:
        logger.exception("image insert error")
        db.rollback()
        result = None
    return result


### category
def select_category(db: Session, **kwargs: Dict) -> Optional[schema.Category]:
    dao = schema.Category
    try:
        res = dao.get(db, **kwargs)
    except Exception:
        logger.exception("category select error")
        res = None
    return res


### task
def insert_task(db: Session, **kwargs: Dict) -> Optional[schema.Task]:
    dao = schema.Task
    try:
        result = dao.create(db, kwargs=kwargs)
    except Exception:
        logger.exception("task insert error")
        return None
    return result


def update_task(
    db: Session, pkey: int, data: models.UpdateTask
) -> Optional[schema.Task]:
    dao = schema.Task
    try:
        result = dao.update(db, id=pkey, **data.dict())
    except Exception:
        logger.exception("task update error")
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
    except Exception:
        logger.exception("inference insert error")
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
    res = query.all()
    return res


def insert_inference_result(
    db: Session,
    data: Dict,
) -> bool:
    inference_result = data.get("inference_result", {})
    response_log = inference_result.get("response_log", {})
    try:
        db.add(
            schema.Inference(
                task_id=data.get("task_id"),
                image_id=data.get("image_id"),
                inference_result=inference_result,
                inference_type=data.get("inference_type"),
                start_datetime=response_log.get("inference_start_time"),
                finish_datetime=response_log.get("inference_end_time"),
                inference_img_path=response_log.get("image_path"),
            )
        )
        db.commit()
    except Exception:
        logger.exception("inference result insert error")
        db.rollback()
        return False
    return True


def insert_training_dataset(
    db: Session, **kwargs: Dict
) -> Union[Tuple[int, str], Tuple[None, None]]:
    try:
        res = schema.Dataset.create(db, kwargs=kwargs)
    except Exception:
        logger.exception("training dataset insert error")
        res = None
    if res:
        return (res.dataset_pkey, res.dataset_id)
    return (None, None)


def insert_category(db: Session, **kwargs: Dict) -> Optional[int]:
    try:
        res = schema.Category.create(db, kwrargs=kwargs)
    except:
        logger.exception("category insert error")
        db.rollback()
        res = None
    if res:
        return res.category_pkey
    return None


def insert_inference_image(db: Session, **kwargs: Dict) -> Optional[int]:
    try:
        res = schema.Image.create(db, kwargs=kwargs)
    except:
        logger.exception("inference image insert error")
        db.rollback()
        res = None
    if res:
        return res.image_pkey
    return None


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


def select_category_all(db: Session) -> List[schema.Category]:
    """
    SELECT
        *
    FROM
        category
    """
    query = db.query(schema.Category).select_from(schema.Category)
    res = query.all()
    return res


def select_category_by_name(db: Session, category_name: str) -> Optional[int]:
    """
    SELECT
        category_pkey
    FROM
        category
    WHERE
        category_name_en = {category_name}
        or
        category_name_kr = {category_name}
    """
    query = (
        db.query(schema.Category)
        .select_from(schema.Category)
        .filter(
            or_(
                schema.Category.category_name_en == category_name,
                schema.Category.category_name_kr == category_name,
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


def delete_category_cascade_image(db: Session, dataset_pkey: int) -> bool:
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
    query = db.query(schema.Category).filter(schema.Category.is_pretrained == False)

    res = query.all()

    for category in res:
        try:
            q = (
                db.query(schema.Image)
                .filter(
                    and_(
                        schema.Image.category_pkey == category.category_pkey,
                        schema.Image.dataset_pkey == dataset_pkey,
                    )
                )
                .delete()
            )
        except Exception:
            logger.exception("image cascade delete error")
            db.rollback()
            return False

    try:
        query.delete()
    except Exception:
        logger.exception("category cascade delete error")
        db.rollback()
        return False
    db.commit()
    return True
