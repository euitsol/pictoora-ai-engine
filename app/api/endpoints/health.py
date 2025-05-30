from fastapi import APIRouter
from ...schemas.responses import HealthResponse, RootResponse
from ...core.config import settings
from ...core.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.get("/", response_model=RootResponse)
async def root():
    """
    Root Response
    """
    try:
        app_name = settings.APP_NAME
        return RootResponse(
            status_code=1000,
            message="Welcome to "+app_name
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return RootResponse(
            status_code=1001,
            message="System is not healthy",
            error=str(e)
        ) 

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint that returns the current version and status
    """
    try:
        health_data = {
            "version": settings.VERSION,
            "status": "healthy"
        }
        logger.info("Health check performed successfully")
        return HealthResponse(
            status_code=1000,
            message="System is healthy",
            data=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status_code=1001,
            message="System is not healthy",
            error=str(e)
        ) 