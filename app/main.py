import uvicorn
import os
import sys

sys.path.append("/workspace")
from app.utils.generator import create_app


os.environ["API_ENV"] = "production"
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
