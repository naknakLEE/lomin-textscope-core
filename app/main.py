import uvicorn
import os

from app.utils.generator import create_app
from fastapi.testclient import TestClient


os.environ["API_ENV"] = "production"
app = create_app()
TestClient = TestClient(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
