from fastapi import APIRouter
from ...schemas.responses import BaseResponse
from ...core.cache import cache
from ...core.logger import get_logger
from typing import Dict, Any

logger = get_logger()
router = APIRouter()

@router.get("/cache/status", response_model=BaseResponse[Dict[str, Any]])
async def get_cache_status():
    """
    Get the current cache status and contents
    """
    try:
        cache_data = {
            "status": {
                "current_size": len(cache._cache),
                "max_size": cache._cache.maxsize,
                "ttl": getattr(cache._cache, 'ttl', None)
            },
            "entries": {}
        }

        # Iterate through cache entries without TTL calculations
        for key, value in cache._cache.items():
            try:
                cache_data["entries"][str(key)] = {
                    "value": value,
                    "ttl_remaining": None  # TTL removed for compatibility
                }
            except Exception as e:
                logger.warning(f"Error processing cache entry {key}: {str(e)}")
                continue

        logger.info(f"Cache status retrieved successfully with {len(cache_data['entries'])} entries")
        return BaseResponse(
            status_code=6000,
            message="Cache status retrieved successfully",
            data=cache_data
        )
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        return BaseResponse(
            status_code=6001,
            message="Failed to get cache status",
            error=str(e)
        )