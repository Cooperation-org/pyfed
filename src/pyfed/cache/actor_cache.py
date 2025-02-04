"""
Actor cache implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

class ActorCache:
    """Cache for actor data."""

    def __init__(self, cache, ttl: int = 3600):
        """Initialize actor cache."""
        self.cache = cache
        self.ttl = ttl

    async def get(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """Get actor data from cache."""
        return await self.cache.get(f"actor:{actor_id}")

    async def set(self, actor_id: str, actor_data: Dict[str, Any]) -> None:
        """Set actor data in cache."""
        await self.cache.set(f"actor:{actor_id}", actor_data, self.ttl)

    async def delete(self, actor_id: str) -> None:
        """Delete actor data from cache."""
        await self.cache.delete(f"actor:{actor_id}")

    async def clear(self) -> None:
        """Clear all cached actors."""
        await self.cache.clear() 