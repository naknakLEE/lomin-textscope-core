from httpx import AsyncClient

from typing import Dict, Tuple, Optional, List

from app.common import settings
from app.wrapper import model_server_url


supported_class = ["처방전", "보험금청구서"]


async def longinus(
    client: AsyncClient,
    inputs: Dict,
    inference_result: Optional[Dict],
    response_log: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    inference_inputs = inputs
    route_name = inputs.get("route_name")
    classification_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    classification_result = classification_response.json()
    response = dict(
        status_code=classification_response.status_code,
        response=classification_result,
        is_supported_type=True,
    )
    if classification_result.get("doc_type") not in supported_class:
        response["is_supported_type"] = False
    return response


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
        image_size=inference_result["image_size"],
    )
    classification_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    classification_result = classification_response.json()
    response = dict(
        status_code=classification_response.status_code,
        response=classification_result,
        is_supported_type=True,
    )
    if classification_result.get("doc_type") not in supported_class:
        response["is_supported_type"] = False
    return response
