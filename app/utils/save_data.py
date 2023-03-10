from os import environ
from datetime import datetime
from sqlalchemy.orm import Session

from app import models
from app.database import query
from app.utils.logging import logger

from dotenv import load_dotenv

load_dotenv("/workspace/.env")


async def save_updated_task(db: Session, doc_type: str, task_pkey: int) -> None:
    category = query.select_category(db, kwargs=dict(inference_doc_type=doc_type))
    if category:
        pkey = category.pkey
        update_data = models.UpdateTask(category_pkey=pkey)
        query.update_task(db, pkey=task_pkey, data=update_data)


async def save_inference_results(
    db: Session,
    task_pkey: int,
    inference_img_path: str,
    inference_results: dict,
) -> None:
    artifact_name_list = list(
        map(lambda x: x.strip(), environ.get("ARTIFACT_NAME_LIST", "").split(","))
    )
    for key, inference_result in inference_results.items():
        logger.info(f"inference key: {inference_result}")
        response_log = inference_result.get("response_log", {})
        if response_log is None:
            response_log = dict()
        # @TODO: model name이 response_log에 안들어 있음
        model_name = None
        for artifact_name in artifact_name_list:
            start_time = f"{artifact_name}_start_time"
            end_time = f"{artifact_name}_end_time"
            if start_time in response_log.keys():
                model_name = artifact_name
                start_datetime = response_log.get(start_time)
            else:
                start_datetime = None
            if end_time in response_log.keys():
                finish_datetime = response_log.get(end_time)
            else:
                finish_datetime = None

        if model_name is None:
            inference_type = "err"
            inference_sequence = 0
        else:
            inference_type = models.InferenceTypeEnum[model_name.upper()].value
            inference_sequence = models.InferenceSequenceEnum[model_name.upper()].value

        create_data = dict(
            task_pkey=task_pkey,
            inference_img_path=inference_img_path,
            inference_type=inference_type,
            inference_result=inference_result,
            inference_sequence=inference_sequence,
        )

        if start_datetime:
            create_data.update(
                dict(
                    start_datetime=datetime.strptime(
                        start_datetime, "%Y-%m-%d %H:%M:%S"
                    )
                )
            )
        if finish_datetime:
            create_data.update(
                dict(
                    finish_datetime=datetime.strptime(
                        finish_datetime, "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

        inference_log = models.CreateInference(**create_data)
        query.insert_inference(db, inference_log)
