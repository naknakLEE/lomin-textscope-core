import json
from requests.sessions import session
from sqlalchemy.orm import Session


from app import models
from app.database import schema

from app.database.connection import Base


def create_db_table(db: Session) -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
    finally:
        session.close()

def get_image_path(db: Session, image_id: str):
    '''
    SELECT
        image.image_path
    FROM
        image
    WHERE image.image_id = 'ttt-ttt-ttt-ttt'
    '''
    query = db\
        .query(schema.Image.image_path)\
        .select_from(schema.Image)\
        .filter(schema.Image.image_id == image_id)

    res = query.first()[0]
    return res

def get_root_dir(db: Session, dataset_id: str):
    '''
    SELECT
        dataset.root_path
    FROM
        dataset
    WHERE
        dataset.dataset_id = 'aaa-aaa-aaa'
    '''

    query = db\
        .query(schema.Dataset.root_path)\
        .select_from(schema.Dataset)\
        .filter(schema.Dataset.dataset_id == dataset_id)\
        
    res = query.first()[0]
    return res

def insert_inference_result(db: Session, task_id: str, inferenec_result: json, inference_type: str, image_pkey: int):
    '''
            INSERT INTO
            inference
        (
            task_id,
            inference_result,
            inference_type,
            image_pkey
        )
        VALUES
        (
            'test1',
            '{"test" : "test"}',
            'gocr',
            1
        )
    '''
    try:
        db.add(schema.Inference(task_id = task_id, inferenec_result = inferenec_result, inference_type = inference_type, image_pkey = image_pkey))
        db.commit()  
    except:
        db.rollback()
        return False
    return True