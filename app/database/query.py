import json
from requests.sessions import session
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc


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

def insert_image(db: Session, data: models.CreateImage):
    dao = schema.Image
    try:
        result = dao.create(db, **data.dict())
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
def insert_task(db: Session, data: models.CreateTask):
    dao = schema.Task
    try:
        result = dao.create(db, **data.dict())
    except Exception as e:
        logger.warning(f'task insert error: {e}')
        db.rollback()
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
def insert_inference(db: Session, data: models.CreateInference):
    dao = schema.Inference
    try:
        result = dao.create(db, **data.dict())
    except Exception as e:
        logger.warning(f'inference insert error: {e}')
        db.rollback()
        return False
    return result