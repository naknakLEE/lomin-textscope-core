from httpx import AsyncClient

from typing import Dict, Tuple, Optional

from app.common import settings
from app.wrapper import model_server_url, pp


async def tiamo(
    client: AsyncClient,
    inputs: Dict,
    inference_result: Dict,
    response_log: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    route_name = inputs.get("route_name")
    inference_inputs = dict(
        valid_boxes=inference_result.get("boxes", []),
        classes=inference_result.get("classes", []),
        image_path=inputs.get("image_path"),
        page=inputs.get("page"),
    )
    recognition_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    recognition_result = recognition_response.json()
    rec_preds = recognition_result.get("rec_preds")
    recognition_result["texts"] = await pp.convert_preds_to_texts(client, rec_preds)
    return dict(
        status_code=recognition_response.status_code,
        response=recognition_result,
    )
