from fastapi import FastAPI
from database import init_models
from routers import upload, summary

app = FastAPI()

#this function runs once at app startup, create tables from models (due to init_models)
@app.on_event("startup")
async def startup():
    await init_models()

#upload.router is the APIRouter object defined in routers/upload.py
app.include_router(upload.router, prefix="/upload", tags=["upload"])

app.include_router(summary.router, prefix="/summary", tags=["summary"])