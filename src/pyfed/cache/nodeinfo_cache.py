"""
NodeInfo caching implementation.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import aioredis
import json

from ..utils.exceptions import CacheError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class NodeInfoCache:
    """NodeInfo cache implementation."""

    def __init__(self,
                 redis_url: str = "redis://localhost",
                 ttl: int = 3600):  # 1 hour default
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis = None

    async def initialize(self) -> None:
        """Initialize cache."""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize NodeInfo cache: {e}")
            raise CacheError(f"Cache initialization failed: {e}")

    async def get(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get cached NodeInfo."""
        try:
            if not self.redis:
                return None
                
            key = f"nodeinfo:{domain}"
            data = await self.redis.get(key)
            return json.loads(data) if data else None
            
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None

    async def set(self, domain: str, data: Dict[str, Any]) -> None:
        """Cache NodeInfo data."""
        try:
            if not self.redis:
                return
                
            key = f"nodeinfo:{domain}"
            await self.redis.set(
                key,
                json.dumps(data),
                ex=self.ttl
            )
            
        except Exception as e:
            logger.error(f"Failed to cache NodeInfo: {e}")

    async def close(self) -> None:
        """Clean up resources."""
        if self.redis:
            await self.redis.close() 