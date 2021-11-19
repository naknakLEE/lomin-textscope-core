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

def select_image(db: Session, image_id: str):
    '''
    SELECT
        *
    FROM
        image
    WHERE 
        image_id = 'ttt-ttt-ttt-ttt'
    '''
    query = db\
        .query(schema.Image)\
        .select_from(schema.Image)\
        .filter(schema.Image.image_id == image_id)

    res = query.all()
    return res

def select_dataset(db: Session, dataset_id: str):
    '''
    SELECT
        *
    FROM
        dataset
    WHERE 
        dataset_id = 'ttt-ttt-ttt-ttt'
    '''

    query = db\
        .query(schema.Dataset)\
        .select_from(schema.Dataset)\
        .filter(schema.Dataset.dataset_id == dataset_id)\
        
    res = query.all()
    return res

def select_category(db: Session, model_id: str):
    '''
    SELECT 
        *
    FROM
        category
    JOIN
        model 
    ON
        category.model_pkey = category.model_pkey
    WHERE 
        model_id = 'model1'
    '''

    query = db\
        .query(schema.Category, schema.Model)\
        .select_from(schema.Category)\
        .join(schema.Model, schema.Category.model_pkey == schema.Model.model_pkey)\
        .filter(schema.Model.model_id == model_id)\
        
    res = query.all()
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

def insert_training_dataset(db: Session, task_id: str, inferenec_result: json, inference_type: str, image_pkey: int):
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
    
def insert_inference_image(db: Session, **kwargs):
    '''
        #TODO sql 작성
    '''
    try:
        db.add(schema.Inference(**kwargs))
        db.commit()  
    except:
        db.rollback()
        return False
    return True
    
