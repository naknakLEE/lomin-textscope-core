from typing import List
from datetime import datetime

from app.utils.utils import cal_time_elapsed_seconds
from app.database.schema import ModelInfo


def init():
    response = dict()
    response_log = dict()
    request_datetime = datetime.now()
    
    return response, response_log, request_datetime


def  response_metadata(request_datetime: datetime):
    response_datetime = datetime.now()
    elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
    
    return response_datetime, elapsed


def model2response_data(models: List[ModelInfo]) -> dict():
    res = list()
    for model in models:
        res.append(
            {
                "model_idx" : model.model_idx,
                "model_name_kr" : model.model_name_kr,
                "model_name_en" : model.model_name_en,
                
            }
        )
    return res