import os
import uvicorn

from app.common.const import get_settings
from app.utils.create_app import app_generator

os.environ["API_ENV"] = "production"
settings = get_settings()
app = app_generator()
args = {
    "app": "main:app",
    "host": "0.0.0.0",
    "port": 8000,
}
if settings.DEVELOP:
    args["reload"] = True


if __name__ == "__main__":
    uvicorn.run(**args)
