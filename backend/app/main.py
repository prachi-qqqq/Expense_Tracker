"""FastAPI application entry point."""

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, expenses
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine

# Import all models so Base.metadata has them
from app.models import Expense, IdempotencyKey, User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — create tables on startup."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="Fenmo — Expense Tracker API",
    description="Production-grade expense tracking with idempotent operations",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Log every request with method, path, and duration."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "%s %s → %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions — never expose stack traces."""
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )


# --- Routers ---
app.include_router(auth.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")


# --- Health Check ---
@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}
