"""
In-memory cache implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class MemoryCache:
    """Simple in-memory cache."""

    def __init__(self, ttl: int = 3600):
        """Initialize cache."""
        self.data: Dict[str, Any] = {}
        self.expires: Dict[str, datetime] = {}
        self.ttl = ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.data:
            return None
            
        # Check expiration
        if datetime.utcnow() > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return None
            
        return self.data[key]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        self.data[key] = value
        self.expires[key] = datetime.utcnow() + timedelta(
            seconds=ttl if ttl is not None else self.ttl
        )

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self.data.pop(key, None)
        self.expires.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        self.data.clear()
        self.expires.clear() 