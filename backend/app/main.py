from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api import admin, assistant, auth, dashboard, detect, history, log, model
from app.core.config import settings
from app.core.response import AppException, error_response
from app.core.task_queue import task_queue
from app.db.init_db import create_tables, ensure_storage_dirs, init_db
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_storage_dirs()
    create_tables()
    db: Session = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    task_queue.start()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return error_response(exc.code, exc.message, exc.http_status)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return error_response(42200, str(exc), 422)


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, exc: Exception):
    return error_response(50000, str(exc), 500)


@app.get("/health")
def health():
    return {"code": 0, "message": "success", "data": {"status": "ok"}}


app.include_router(auth.router, prefix="/api")
app.include_router(detect.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(model.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(log.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
