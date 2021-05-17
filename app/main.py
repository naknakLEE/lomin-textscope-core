import uvicorn

from fastapi import FastAPI

from routes import auth, index, users, inference


# API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

app = FastAPI()

app.include_router(index.router)
app.include_router(inference.router, tags=["inference"])
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
