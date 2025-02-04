"""
Cached storage backend implementation.
Provides caching layer on top of any storage backend.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass
from enum import Enum

from .base import StorageBackend
from ..utils.exceptions import StorageError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class CacheStrategy(Enum):
    """Cache strategies."""
    WRITE_THROUGH = "write_through"  # Write to cache and storage simultaneously
    WRITE_BACK = "write_back"        # Write to cache first, then storage async
    WRITE_AROUND = "write_around"    # Write directly to storage, update cache later

@dataclass
class CacheConfig:
    """Cache configuration."""
    strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    ttl: int = 3600  # Default 1 hour TTL
    max_size: int = 10000  # Maximum number of cached items
    update_factor: float = 0.5  # Update cache when TTL * update_factor remains

class CachedStorageBackend(StorageBackend):
    """
    Cached storage backend implementation.
    Provides caching layer on top of any storage backend.
    """
    
    def __init__(
        self,
        primary_backend: StorageBackend,
        cache_backend: StorageBackend,
        config: Optional[CacheConfig] = None
    ):
        self.primary = primary_backend
        self.cache = cache_backend
        self.config = config or CacheConfig()
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0
        }
        
    async def initialize(self) -> None:
        """Initialize storage backends."""
        await self.primary.initialize()
        await self.cache.initialize()
        
    async def create_activity(self, activity: Dict[str, Any]) -> str:
        """Create activity with caching."""
        activity_id = activity.get('id')
        if not activity_id:
            raise StorageError("Activity must have an ID")
            
        if self.config.strategy == CacheStrategy.WRITE_THROUGH:
            # Write to both cache and storage
            await asyncio.gather(
                self.cache.create_activity(activity),
                self.primary.create_activity(activity)
            )
            
        elif self.config.strategy == CacheStrategy.WRITE_BACK:
            # Write to cache first
            await self.cache.create_activity(activity)
            # Schedule storage write
            asyncio.create_task(self.primary.create_activity(activity))
            
        else:  # WRITE_AROUND
            # Write directly to storage
            await self.primary.create_activity(activity)
            # Schedule cache update
            asyncio.create_task(self.cache.create_activity(activity))
            
        self._cache_stats["writes"] += 1
        return activity_id
        
    async def get_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Get activity with caching."""
        # Try cache first
        activity = await self.cache.get_activity(activity_id)
        if activity:
            self._cache_stats["hits"] += 1
            return activity
            
        # Cache miss, get from storage
        self._cache_stats["misses"] += 1
        activity = await self.primary.get_activity(activity_id)
        if activity:
            # Update cache
            await self.cache.create_activity(activity)
            
        return activity
        
    async def create_object(self, obj: Dict[str, Any]) -> str:
        """Create object with caching."""
        object_id = obj.get('id')
        if not object_id:
            raise StorageError("Object must have an ID")
            
        if self.config.strategy == CacheStrategy.WRITE_THROUGH:
            await asyncio.gather(
                self.cache.create_object(obj),
                self.primary.create_object(obj)
            )
            
        elif self.config.strategy == CacheStrategy.WRITE_BACK:
            await self.cache.create_object(obj)
            asyncio.create_task(self.primary.create_object(obj))
            
        else:  # WRITE_AROUND
            await self.primary.create_object(obj)
            asyncio.create_task(self.cache.create_object(obj))
            
        self._cache_stats["writes"] += 1
        return object_id
        
    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Get object with caching."""
        obj = await self.cache.get_object(object_id)
        if obj:
            self._cache_stats["hits"] += 1
            return obj
            
        self._cache_stats["misses"] += 1
        obj = await self.primary.get_object(object_id)
        if obj:
            await self.cache.create_object(obj)
            
        return obj
        
    async def bulk_create_activities(
        self,
        activities: List[Dict[str, Any]]
    ) -> List[str]:
        """Bulk create activities."""
        activity_ids = []
        
        if self.config.strategy == CacheStrategy.WRITE_THROUGH:
            # Create in both cache and storage
            cache_task = self.cache.bulk_create_activities(activities)
            storage_task = self.primary.bulk_create_activities(activities)
            await asyncio.gather(cache_task, storage_task)
            
        elif self.config.strategy == CacheStrategy.WRITE_BACK:
            # Write to cache first
            await self.cache.bulk_create_activities(activities)
            # Schedule storage write
            asyncio.create_task(self.primary.bulk_create_activities(activities))
            
        else:  # WRITE_AROUND
            # Write directly to storage
            await self.primary.bulk_create_activities(activities)
            # Schedule cache update
            asyncio.create_task(self.cache.bulk_create_activities(activities))
            
        self._cache_stats["writes"] += len(activities)
        return [a.get('id') for a in activities if a.get('id')]
        
    async def bulk_create_objects(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[str]:
        """Bulk create objects."""
        object_ids = []
        
        if self.config.strategy == CacheStrategy.WRITE_THROUGH:
            cache_task = self.cache.bulk_create_objects(objects)
            storage_task = self.primary.bulk_create_objects(objects)
            await asyncio.gather(cache_task, storage_task)
            
        elif self.config.strategy == CacheStrategy.WRITE_BACK:
            await self.cache.bulk_create_objects(objects)
            asyncio.create_task(self.primary.bulk_create_objects(objects))
            
        else:  # WRITE_AROUND
            await self.primary.bulk_create_objects(objects)
            asyncio.create_task(self.cache.bulk_create_objects(objects))
            
        self._cache_stats["writes"] += len(objects)
        return [o.get('id') for o in objects if o.get('id')]
        
    async def get_collection(
        self,
        collection_id: str,
        page_size: int = 20,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get paginated collection.
        Returns (items, next_cursor).
        """
        # Try cache first
        result = await self.cache.get_collection(
            collection_id,
            page_size,
            cursor
        )
        
        if result[0]:  # Cache hit
            self._cache_stats["hits"] += 1
            return result
            
        # Cache miss
        self._cache_stats["misses"] += 1
        result = await self.primary.get_collection(
            collection_id,
            page_size,
            cursor
        )
        
        if result[0]:  # Cache collection page
            items, next_cursor = result
            await self.cache.bulk_create_objects(items)
            
        return result
        
    async def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self._cache_stats.copy()
        
    async def clear_cache(self) -> None:
        """Clear the cache."""
        await self.cache.clear()
        self._cache_stats = {k: 0 for k in self._cache_stats}
