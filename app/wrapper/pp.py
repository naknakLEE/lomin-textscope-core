from httpx import Client

from typing import Dict, Tuple, List
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from app.common import settings
from app.wrapper import pp_server_url


def post_processing(
    client: Client,
    inference_results: Dict,
    post_processing_type: str,
    response_log: Dict,
    request_id: str,
) -> Tuple[int, Dict, Dict]:
    post_processing_start_time = datetime.now()
    response_log.update(
        post_processing_start_time=post_processing_start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    inference_results["img_size"] = (
        inference_results["image_height"],
        inference_results["image_width"],
    )
    pp_response = client.post(
        f"{pp_server_url}/post_processing/{post_processing_type}",
        json=inference_results,
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