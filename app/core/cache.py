from typing import Any, Optional
from cachetools import TTLCache
from .logger import get_logger

logger = get_logger()

class CacheManager:
    def __init__(self, ttl: int = 3600, maxsize: int = 1000):
        """
        Initialize cache with TTL (time-to-live) in seconds and maximum size
        :param ttl: Time to live in seconds (default 1 hour)
        :param maxsize: Maximum number of items in cache (default 1000)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.info(f"Cache initialized with TTL: {ttl}s, maxsize: {maxsize}")

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a value in cache. If expire is provided, it will override the default TTL.
        :param key: Cache key
        :param value: Value to cache
        :param expire: Optional custom expiration time in seconds
        :return: True if successful, False otherwise
        """
        try:
            if expire:
                # If custom expiration provided, create a new cache just for this item
                temp_cache = TTLCache(maxsize=1, ttl=expire)
                temp_cache[key] = value
                self._cache[key] = temp_cache[key]
            else:
                self._cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        :param key: Cache key
        :return: Cached value or None if not found
        """
        try:
            return self._cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cache: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a value from cache
        :param key: Cache key
        :return: True if successful, False otherwise
        """
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries
        :return: True if successful, False otherwise
        """
        try:
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    @property
    def currsize(self) -> int:
        """
        Get current number of items in cache
        :return: Number of items
        """
        return len(self._cache)

# Create a global cache instance with 1-hour TTL and 1000 items max
cache = CacheManager() 