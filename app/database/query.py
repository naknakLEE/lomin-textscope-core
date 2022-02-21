import json
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_


from app import models
from app.database import schema
from app.utils.logging import logger
from app.database.connection import Base
from app.utils.utils import print_error_log


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
    except Exception as ex:
        logger.error(ex)
    finally:
        session.close()


### image
def select_image_by_pkey(db: Session, image_pkey: str) -> schema.Image:
    query = (
        db.query(schema.Image)
        .select_from(schema.Image)
        .filter(schema.Image.image_pkey == image_pkey)
    )
    res = query.first()
    return res


def select_image_all(db: Session):
    """
    SELECT
        *
    FROM
        image
    """
    dao = schema.Image
    try:
        res = dao.get_all(db)
    except Exception as e:
        logger.warning(f"image select error: {e}")
        res = None
    return res


def select_image(db: Session, **kwargs):
    dao = schema.Image
    try:
        res = dao.get(db, **kwargs)
    except Exception as e:
        logger.warning(f"image select error: {e}")
        res = None
    return res


def insert_image(db: Session, **kwargs):
    dao = schema.Image
    try:
        result = dao.create(db, **kwargs)
    except Exception as e:
        logger.warning(f"image insert error: {e}")
        db.rollback()
        return False
    return result


### category
def select_category(db: Session, **kwargs):
    dao = schema.Category
    try:
        res = dao.get(db, **kwargs)
    except Exception as e:
        logger.warning(f"category select error: {e}")
        res = None
    return res


### task
def insert_task(session: Session, data):
    dao = schema.Task
    try:
        result = dao.create(session, **data)
    except Exception:
        print_error_log()
        # logger.warning(f'task insert error: {e}')
        # db.rollback()
        return False
    return result


def update_task(db: Session, pkey: int, data: models.UpdateTask):
    dao = schema.Task
    try:
        result = dao.update(db, pkey=pkey, **data.dict())
    except Exception as e:
        logger.warning(f"task update error: {e}")
        db.rollback()
        return False
    return result


### inference
def insert_inference(db: Session, data: models.CreateInference):
    dao = schema.Inference
    try:
        result = dao.create(db, **data.dict())
    except Exception as e:
        logger.warning(f"inference insert error: {e}")
        db.rollback()
        return False
    return result


def select_inference_by_type(db: Session, inference_type: str):
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.inference_type == inference_type)
    )
    res = query.all()
    return res


def select_dataset(db: Session, dataset_id: str):
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
):
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
    except Exception as ex:
        logger.warning(f"insert error: {ex}")
        db.rollback()
        return False


def insert_training_dataset(db: Session, **kwargs):
    res = schema.Dataset.create(db, **kwargs)
    if res:
        return res.dataset_pkey, res.dataset_id


def insert_category(db: Session, **kwargs):
    res = schema.Category.create(db, **kwargs)
    if res:
        return res.category_pkey


def insert_inference_image(db: Session, **kwargs):
    res = schema.Image.create(db, **kwargs)
    if res:
        return res.image_pkey


def select_inference_img_path_from_taskid(db: Session, task_id: str):
    query = (
        db.query(schema.Visualize.inference_img_path)
        .select_from(schema.Visualize)
        .filter(schema.Visualize.task_id == task_id)
    )
    res = query.first()
    return res


def delete_dataset(db: Session, dataset_id: str):
    try:
        query = db.query(schema.Dataset).filter_by(dataset_id=dataset_id).delete()
    except Exception as ex:
        db.rollback()
        logger.warning(f"delete error: {ex}")
        return False

    db.commit()
    return True


def select_inference_all(db: Session):
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


def delete_inference_all(db: Session):
    try:
        db.query(schema.Inference).delete()
    except Exception as ex:
        logger.warning(f"delete error: {ex}")
        db.rollback()
        return False
    return True


def select_category_pkey(db: Session, dataset_id: str):
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


def select_inference_image(db: Session, task_id: str):
    query = (
        db.query(schema.Inference, schema.Image)
        .select_from(schema.Inference)
        .join(schema.Image, schema.Inference.image_pkey == schema.Image.image_pkey)
        .filter(schema.Inference.task_id == task_id)
    )
    res = query.all()
    return res


def select_gocr_inference_from_taskid(db: Session, task_id: str):
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.task_id == task_id)
        .filter(schema.Inference.inference_type == "gocr")
    )

    res = query.all()
    return res


def select_kv_inference_from_taskid(db: Session, task_id: str):
    query = (
        db.query(schema.Inference)
        .select_from(schema.Inference)
        .filter(schema.Inference.task_id == task_id)
        .filter(schema.Inference.inference_type == "kv")
    )

    res = query.first()
    return res


def select_category_all(db: Session):
    """
    SELECT
        *
    FROM
        category
    """
    query = db.query(schema.Category).select_from(schema.Category)
    res = query.all()
    return res


def select_category_by_name(db: Session, category_name: str) -> int:
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
    return res.category_pkey


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
            logger.info(f"delete test: {category.category_pkey, q}")
        except Exception as ex:
            db.rollback()
            logger.warning(f"delete error: {ex}")
            return False

    try:
        query.delete()
    except Exception as ex:
        db.rollback()
        logger.warning(f"delete error: {ex}")
        return False
    db.commit()
    return True
