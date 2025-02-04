"""
Base storage interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from ..utils.exceptions import StorageError

class StorageProvider(Enum):
    """Storage provider types."""
    MEMORY = "memory"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    REDIS = "redis"

class StorageBackend(ABC):
    """Abstract storage backend."""

    # Register storage backends
    _providers = {}

    @classmethod
    def register_provider(cls, provider_name: str, provider_class: type):
        """Register a storage provider."""
        cls._providers[provider_name] = provider_class

    @classmethod
    def create(cls, provider: str, **kwargs) -> 'StorageBackend':
        """Create storage backend instance."""
        if provider not in cls._providers:
            raise StorageError(f"Unsupported storage provider: {provider}")
        
        provider_class = cls._providers[provider]
        return provider_class(**kwargs)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize storage."""
        pass

    @abstractmethod
    async def create_activity(self, activity: Dict[str, Any]) -> str:
        """Store an activity."""
        pass

    @abstractmethod
    async def get_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Get an activity by ID."""
        pass

    @abstractmethod
    async def create_object(self, obj: Dict[str, Any]) -> str:
        """Store an object."""
        pass

    @abstractmethod
    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Get an object by ID."""
        pass

    @abstractmethod
    async def delete_object(self, object_id: str) -> bool:
        """Delete an object."""
        pass

    @abstractmethod
    async def update_object(self, object_id: str, obj: Dict[str, Any]) -> bool:
        """Update an object."""
        pass

    @abstractmethod
    async def list_activities(self, 
                            actor_id: Optional[str] = None,
                            activity_type: Optional[str] = None,
                            limit: int = 20,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """List activities with optional filtering."""
        pass

    @abstractmethod
    async def list_objects(self,
                          object_type: Optional[str] = None,
                          attributed_to: Optional[str] = None,
                          limit: int = 20,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """List objects with optional filtering."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close storage connection."""
        pass