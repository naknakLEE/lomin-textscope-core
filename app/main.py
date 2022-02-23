import os

os.environ["API_ENV"] = "dev"
import uvicorn

from app.common.const import get_settings
from app.utils.create_app import app_generator


settings = get_settings()


app = app_generator()
args = {
    "app": "main:app",
    "host": "0.0.0.0",
    "port": settings.WEB_IP_PORT,
    "workers": settings.TEXTSCOPE_CORE_WORKERS,
}
if settings.DEVELOP:
    args["reload"] = True


if __name__ == "__main__":
    uvicorn.run(**args)
