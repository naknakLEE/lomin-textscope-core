from httpx import Client

from typing import Dict, Tuple

from app.common import settings


rotate_server_url = f"http://serving:{settings.ROTATE_SERVICE_PORT}"


def longinus(
    client: Client,
    inputs: Dict,
    route_name: str = "rotate",
) -> Tuple[int, Dict]:
    rotate_response = client.post(
        f"{rotate_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    rotate_result = rotate_response.json()
    response = dict(
        status_code=rotate_response.status_code,
        response=rotate_result,
    )
    return response

