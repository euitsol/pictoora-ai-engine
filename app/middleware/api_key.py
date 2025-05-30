from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from ..core.config import settings
from ..core.logger import get_logger

logger = get_logger()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request) -> Optional[str]:
    if request.url.path == "/api/v1/health":
        return None
        
    api_key = await api_key_header(request)
    
    if not settings.API_KEY:
        logger.warning("No API key set in environment, skipping API key check")
        return None
        
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key header missing"
        )
        
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
        
    return api_key 