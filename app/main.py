import os
import sys
import uvicorn

from pathlib import Path
from minio import Minio
# possible app import 
sys.path.append(str(Path(os.getcwd()).parent))
from app.common.const import get_settings
from app.utils.create_app import app_generator


settings = get_settings()
app = app_generator()


@app.on_event("startup")
async def startup_event():
    os.environ["IS_READY"] = "true"


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
