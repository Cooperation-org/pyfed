"""
Base activity handler implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.exceptions import HandlerError, ValidationError
from ..utils.logging import get_logger
from ..storage.base import StorageBackend
from ..federation.resolver import ActivityPubResolver
from ..federation.delivery import ActivityDelivery
# from ..monitoring.decorators import monitor, trace_async
from ..content.handler import ContentHandler  # Instead of individual imports

logger = get_logger(__name__)

class ActivityHandler(ABC):
    """Base activity handler."""

    def __init__(self,
                 storage: StorageBackend,
                 resolver: ActivityPubResolver,
                 delivery: ActivityDelivery):
        self.storage = storage
        self.resolver = resolver
        self.delivery = delivery

    @abstractmethod
    async def validate(self, activity: Dict[str, Any]) -> None:
        """
        Validate activity.
        
        Args:
            activity: Activity to validate
            
        Raises:
            ValidationError if validation fails
        """
        pass

    @abstractmethod
    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """
        Process activity.
        
        Args:
            activity: Activity to process
            
        Returns:
            Activity ID if successful
            
        Raises:
            HandlerError if processing fails
        """
        pass

    # @monitor("activity.handle")
    # @trace_async("activity.handle")
    async def handle(self, activity: Dict[str, Any]) -> Optional[str]:
        """
        Handle activity.
        
        Args:
            activity: Activity to handle
            
        Returns:
            Activity ID if successful
            
        Raises:
            HandlerError if handling fails
        """
        try:
            # Pre-handle operations
            await self.pre_handle(activity)
            
            # Validate activity
            await self.validate(activity)
            
            # Process activity
            result = await self.process(activity)
            
            # Post-handle operations
            await self.post_handle(activity)
            
            return result
            
        except (ValidationError, HandlerError):
            raise
        except Exception as e:
            logger.error(f"Handler error: {e}")
            raise HandlerError(f"Failed to handle activity: {e}")

    async def pre_handle(self, activity: Dict[str, Any]) -> None:
        """Pre-handle operations."""
        pass

    async def post_handle(self, activity: Dict[str, Any]) -> None:
        """Post-handle operations."""
        pass