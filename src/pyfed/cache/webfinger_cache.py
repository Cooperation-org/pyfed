"""
WebFinger cache implementation.
Provides caching for WebFinger lookups to reduce network requests.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
from ..utils.logging import get_logger
from .memory_cache import MemoryCache

logger = get_logger(__name__)

class WebFingerCache:
    """Cache for WebFinger lookups."""
    
    def __init__(self, ttl: int = 3600):  # 1 hour default TTL
        """Initialize WebFinger cache.
        
        Args:
            ttl: Cache TTL in seconds
        """
        self.cache = MemoryCache(ttl)
        
    async def get(self, resource: str) -> Optional[Dict[str, Any]]:
        """Get WebFinger data from cache.
        
        Args:
            resource: WebFinger resource URI
            
        Returns:
            Cached WebFinger data or None if not found
        """
        return await self.cache.get(resource)
        
    async def set(self, resource: str, data: Dict[str, Any]) -> None:
        """Cache WebFinger data.
        
        Args:
            resource: WebFinger resource URI
            data: WebFinger data to cache
        """
        await self.cache.set(resource, data)
        
    async def delete(self, resource: str) -> None:
        """Remove WebFinger data from cache.
        
        Args:
            resource: WebFinger resource URI to remove
        """
        await self.cache.delete(resource)
        
    async def clear(self) -> None:
        """Clear all cached WebFinger data."""
        await self.cache.clear()