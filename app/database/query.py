import json
from typing import Dict
from requests.sessions import session
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc


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
        with open('/workspace/assets/heungkuklife.json', "r") as f:
            json_database_initial_data = json.load(f)
        database_initial_data = json_database_initial_data['DATABASE_INITIAL_DATA']
        for object_table in Base.metadata.sorted_tables:
            table_initial_data = database_initial_data[object_table.name]
            if len(table_initial_data) == 0:
                continue
            if db._engine.execute(f"SELECT count(*) FROM {object_table.name}").scalar() == 0:
                db._engine.execute(object_table.insert(), table_initial_data)
    except Exception as ex:
        logger.error(ex)
    finally:
        session.close()


### image
def select_image_all(db: Session):
    '''
    SELECT
        *
    FROM
        image
    '''
    dao = schema.Image
    try:
        res = dao.get_all(db)
    except Exception as e:
        logger.warning(f'image select error: {e}')
        res = None
    return res

def select_image(db: Session, **kwargs):
    dao = schema.Image
    try:
        res = dao.get(db, **kwargs)
    except Exception as e:
        logger.warning(f'image select error: {e}')
        res = None
    return res


def insert_image(db: Session, data):
    dao = schema.Image
    try:
        result = dao.create(db, **data)
    except Exception as e:
        logger.warning(f'image insert error: {e}')
        db.rollback()
        return False
    return result


### category
def select_category(db: Session, **kwargs):
    dao = schema.Category
    try:
        res = dao.get(db, **kwargs)
    except Exception as e:
        logger.warning(f'category select error: {e}')
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
        logger.warning(f'task update error: {e}')
        db.rollback()
        return False
    return result

### inference
# def insert_inference(db: Session, data: models.CreateInference):
#     dao = schema.Inference
#     try:
#         result = dao.create(db, **data.dict())
#     except Exception as e:
#         logger.warning(f'inference insert error: {e}')
#         db.rollback()
#         return False
#     return result

def insert_inference_result(
    db: Session, 
    data: Dict,
):
    inference_result = data.get("inference_result", {})
    response_log = inference_result.get("response_log", {})
    try:
        db.add(schema.Inference(
            task_id=data.get("task_id"), 
            image_id=data.get("image_id"),
            inference_result=inference_result, 
            inference_type=data.get("inference_type"), 
            start_datetime=response_log.get("inference_start_time"),
            finish_datetime=response_log.get("inference_end_time"),
            inference_img_path=response_log.get("image_path")

        ))
        db.commit()  
    except Exception as ex:
        logger.warning(f"insert error: {ex}")
        db.rollback()
        return False