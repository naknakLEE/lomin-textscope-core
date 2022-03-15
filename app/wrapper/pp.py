from httpx import Client

from typing import Dict, Tuple, List
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from app.common import settings
from app.wrapper import pp_server_url


def post_processing(
    client: Client,
    inputs: Dict,
    post_processing_type: str,
    response_log: Dict,
    task_id: str,
) -> Tuple[int, Dict, Dict]:
    post_processing_start_time = datetime.now()
    response_log.update(
        post_processing_start_time=post_processing_start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    inputs["img_size"] = (
        inputs["image_height"],
        inputs["image_width"],
    )
    pp_response = client.post(
        f"{pp_server_url}/post_processing/{post_processing_type}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
    )
    post_processing_end_time = datetime.now()
    response_log.update(
        dict(
            post_processing_end_time=post_processing_end_time.strftime(
                "%Y-%m-do%d %H:%M:%S"
            ),
            post_processing_time=post_processing_end_time - post_processing_start_time,
        )
    )
    return (pp_response.status_code, pp_response.json(), response_log)


def convert_preds_to_texts(
    client: Client, rec_preds: List, id_type: str = ""
) -> Tuple[int, Dict]:
    request_data = dict(
        rec_preds=rec_preds,
        id_type="",
    )
    convert_response = client.post(
        f"{pp_server_url}/convert/recognition_to_text",
        json=jsonable_encoder(request_data),
        timeout=settings.TIMEOUT_SECOND,
    )
    return (convert_response.status_code, convert_response.json())


def convert_texts_to_preds(
    client: Client, texts: List, id_type: str = ""
) -> Tuple[int, Dict]:
    request_data = dict(
        texts=texts,
        id_type="",
    )
    convert_response = client.post(
        f"{pp_server_url}/convert/text_to_recognition",
        json=jsonable_encoder(request_data),
        timeout=settings.TIMEOUT_SECOND,
    )
    return (convert_response.status_code, convert_response.json())
