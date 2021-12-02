from httpx import AsyncClient

from typing import Dict, Tuple, Optional

from app.common import settings
from app.wrapper import model_server_url


async def general(
    client: AsyncClient,
    inputs: Dict,
    inference_result: Optional[Dict],
    response_log: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    inference_inputs = inputs
    del inference_inputs["model_name"]
    route_name = inputs.get("route_name")
    detection_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    detection_result = detection_response.json()
    return dict(status_code=detection_response.status_code, response=detection_result)


async def duriel(
    client: AsyncClient,
    inputs: Dict,
    inference_result: Dict,
    response_log: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    route_name = inputs.get("route_name")
    inference_inputs = dict(
        scores=inference_result["scores"],
        boxes=inference_result["boxes"],
        texts=inference_result["texts"],
        image_size=(inference_result["image_height"], inference_result["image_width"]),
    )
    detection_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    detection_result = detection_response.json()
    return dict(status_code=detection_response.status_code, response=detection_result)
