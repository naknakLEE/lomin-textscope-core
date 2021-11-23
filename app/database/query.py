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

def select_image_by_pkey(db: Session, image_pkey: str):
    query = db\
        .query(schema.Image)\
        .select_from(schema.Image)\
        .filter(schema.Image.image_pkey == image_pkey)
    res = query.first()
    return res

def select_image_all(db: Session):
    '''
    SELECT
        *
    FROM
        image
    '''
    query = db\
        .query(schema.Image)\
        .select_from(schema.Image)
        
    res = query.all()
    return res

def select_inference_by_type(
    db: Session,
    inference_type: str
):
    query = db\
        .query(schema.Inference)\
        .select_from(schema.Inference)\
        .filter(schema.Inference.inference_type == inference_type)
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

def insert_inference_result(db: Session, task_id: str, inference_result: json, inference_type: str, image_pkey: int):
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
        db.add(schema.Inference(task_id = task_id, inference_result = inference_result, inference_type = inference_type, image_pkey = image_pkey))
        db.commit()  
    except Exception as ex:
        print(f"error {ex}")
        db.rollback()
        return False
    return True

def insert_training_dataset(db: Session, **kwargs):
    res = schema.Dataset.create(db, **kwargs)
    return res.dataset_pkey, res.dataset_id

def insert_category(db: Session, **kwargs):
    res = schema.Category.create(db, **kwargs)
    return res.category_pkey

def insert_image(db: Session, **kwargs):
    res = schema.Image.create(db, **kwargs)
    return res.image_pkey

def insert_inference_image(db: Session, **kwargs):
    res = schema.Image.create(db, **kwargs)
    return res.image_pkey

    
    
def select_category(db: Session, dataset_id: str):
    '''
    select 
        * 
    from
        dataset
    join 
        image
        on
            image.dataset_pkey = dataset.dataset_pkey
    join
        category
        on
            category.category_pkey = image.category_pkey
    where dataset_id = 'eeee'

    '''

    query = db\
        .query(schema.Dataset, schema.Image, schema.Category)\
        .select_from(schema.Dataset)\
        .join(schema.Image, schema.Image.dataset_pkey == schema.Dataset.dataset_pkey)\
        .join(schema.Category, schema.Category.category_pkey == schema.Image.category_pkey)\
        .filter(schema.Dataset.dataset_id == dataset_id)\
        
    res = query.all()
    return res

def delete_dataset(db: Session, dataset_id: str):
    try:
        query = db\
            .query(schema.Dataset)\
            .filter_by(dataset_id=dataset_id).delete()
        return True
    except Exception as ex:
        print(ex)
        return False
        
    

def select_inference_all(db: Session):
    query = db\
        .query(schema.Inference, schema.Image, schema.Category)\
        .select_from(schema.Inference)\
        .join(schema.Image, schema.Image.image_pkey == schema.Inference.image_pkey)\
        .join(schema.Category, schema.Category.category_pkey == schema.Image.category_pkey)

    res = query.all()
    return res


def select_category_pkey(db: Session, dataset_id: str):
    '''
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
    '''
    dataset_pkeys = db\
        .query(schema.Dataset.dataset_pkey)\
        .select_from(schema.Dataset)\
        .filter(schema.Dataset.dataset_id == dataset_id)\
        .all()

    category_pkeys = db\
        .query(schema.Image.category_pkey)\
        .select_from(schema.Image)\
        .filter(schema.Image.dataset_pkey.in_(dataset_pkeys))\
        .distinct()\
        .all()

    query = db\
        .query(schema.Category)\
        .select_from(schema.Category)\
        .filter(schema.Category.category_pkey.in_(category_pkeys))\


    res_category = query.all()
    return res_category

def select_inference_image(db: Session, task_id: str):
    query = db\
        .query(schema.Inference, schema.Image)\
        .select_from(schema.Inference)\
        .join(schema.Image, schema.Inference.image_pkey == schema.Image.image_pkey)\
        .filter(schema.Inference.task_id == task_id)\

    res = query.all()
    return res

def select_gocr_inference_from_taskid(db: Session, task_id: str):
    query = db\
        .query(schema.Inference)\
        .select_from(schema.Inference)\
        .filter(schema.Inference.task_id == task_id)\
    
    res = query.all()
    return res