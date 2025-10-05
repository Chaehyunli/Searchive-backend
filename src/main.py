from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.config import settings
from src.core.exception import (
    CustomException,
    custom_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from alembic.config import Config
from alembic import command
import os

# Initialize FastAPI app
app = FastAPI(
    title="Searchive Backend API",
    description="AI-powered intelligent search and document management system",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Run database migrations on startup"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Welcome to Searchive Backend API",
        "status": "running",
        "environment": settings.APP_ENV,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


# TODO: Include domain routers here as they are created
# Example:
# from src.domains.auth.router import router as auth_router
# from src.domains.documents.router import router as documents_router
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
