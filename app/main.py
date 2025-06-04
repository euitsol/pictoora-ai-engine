from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.logger import get_logger
from .middleware.api_key import verify_api_key
from .api.endpoints import health, upload, process, cache, seo
import os
from pathlib import Path

logger = get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    servers=[
        {"url": settings.APP_URL, "description": "Current server"}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
upload_path = Path("storage/uploads")
upload_path.mkdir(parents=True, exist_ok=True)

# Mount static files directory for uploads
app.mount("/storage/uploads", StaticFiles(directory=str(upload_path.absolute())), name="uploads")

# Add API key middleware
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip API key check for static files
    if request.url.path.startswith(f"storage/uploads"):
        return await call_next(request)
    await verify_api_key(request)
    response = await call_next(request)
    return response

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(process.router, prefix=settings.API_V1_STR)
app.include_router(cache.router, prefix=settings.API_V1_STR)
app.include_router(seo.router, prefix=settings.API_V1_STR)
 
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...") 