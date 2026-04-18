import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, monitoring, questions
from app.config import settings
from app.db.postgres import init_db
from app.middleware import RateLimitMiddleware

logger = logging.getLogger("aimsa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Running in degraded mode.")
    yield


app = FastAPI(
    title="AIMSA - AI Model Service Accelerator",
    description="智能文档问答平台 (RAG)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable", "error": str(exc)},
    )


cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "aimsa", "version": "0.1.0", "status": "running"}
