from fastapi import FastAPI
from database import init_models
from routers import upload

app = FastAPI()

#this function runs once at app startup, create tables from models (due to init_models)
@app.on_event("startup")
async def startup():
    await init_models()

app.include_router(upload.router, prefix="/upload", tags=["upload"])
