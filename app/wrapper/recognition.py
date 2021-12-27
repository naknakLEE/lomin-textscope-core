from httpx import Client

from typing import Dict, Tuple, Optional

from app.common import settings
from app.wrapper import pp


recognition_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.RECOGNITION_SERVICE_PORT}"


def tiamo(
    client: Client,
    inputs: Dict,
    inference_result: Dict,
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    route_name = inputs.get("route_name")
    inference_inputs = dict(
        valid_boxes=inference_result.get("boxes", []),
        classes=inference_result.get("classes", []),
        image_path=inputs.get("image_path"),
        page=inputs.get("page"),
    )
    recognition_response = client.post(
        f"{recognition_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    recognition_result = recognition_response.json()
    rec_preds = recognition_result.get("rec_preds")
    recognition_result["texts"] = pp.convert_preds_to_texts(client, rec_preds)
    return dict(
        status_code=recognition_response.status_code,
        response=recognition_result,
    )
