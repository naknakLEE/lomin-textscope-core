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
    "port": settings.WEB_IP_PORT,
    "workers": settings.TEXTSCOPE_CORE_WORKERS,
}
if settings.DEVELOP:
    args["reload"] = True


# class MyManager(SyncManager):
#     pass


# syncdict = {}


# def get_dict():
#     return syncdict


if __name__ == "__main__":
    # MyManager.register("syncdict", get_dict)
    # manager = MyManager(("0.0.0.0", 12200), authkey=b"password")
    # manager.start()
    uvicorn.run(**args)
