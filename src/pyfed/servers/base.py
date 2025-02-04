"""
Base ActivityPub server implementation.
Provides core functionality for handling activities and managing server state.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..federation.delivery import ActivityDelivery
from ..federation.discovery import InstanceDiscovery
from ..security.key_management import KeyManager
from ..storage.base import BaseStorageBackend
from ..handlers import (
    CreateHandler, FollowHandler, LikeHandler, 
    DeleteHandler, AnnounceHandler, UpdateHandler,
    AcceptHandler, RejectHandler, UndoHandler
)
from ..utils.exceptions import HandlerError, StorageError, DeliveryError

logger = logging.getLogger(__name__)

class ActivityPubServer:
    """
    Base ActivityPub server implementation.
    
    Handles:
    - Activity processing
    - Queue management
    - Storage operations
    - Federation protocols
    """
    
    def __init__(
        self,
        domain: str,
        storage: BaseStorageBackend,
        key_manager: Optional[KeyManager] = None,
        discovery: Optional[InstanceDiscovery] = None,
        delivery: Optional[ActivityDelivery] = None
    ):
        self.domain = domain
        self.storage = storage
        self.key_manager = key_manager or KeyManager(domain=domain)
        self.discovery = discovery or InstanceDiscovery()
        self.delivery = delivery or ActivityDelivery(key_manager=self.key_manager)
        
        # Initialize handlers
        self.handlers = {
            "Create": CreateHandler(storage=storage, delivery=delivery),
            "Follow": FollowHandler(storage=storage, delivery=delivery),
            "Like": LikeHandler(storage=storage, delivery=delivery),
            "Delete": DeleteHandler(storage=storage, delivery=delivery),
            "Announce": AnnounceHandler(storage=storage, delivery=delivery),
            "Update": UpdateHandler(storage=storage, delivery=delivery),
            "Accept": AcceptHandler(storage=storage, delivery=delivery),
            "Reject": RejectHandler(storage=storage, delivery=delivery),
            "Undo": UndoHandler(storage=storage, delivery=delivery)
        }
        
    async def initialize(self) -> None:
        """Initialize server components."""
        await self.key_manager.initialize()
        await self.discovery.initialize()
        await self.delivery.initialize()
        await self.storage.initialize()
        
    async def handle_inbox(self, activity: Dict[str, Any]) -> str:
        """
        Handle incoming activity.
        
        Args:
            activity: ActivityPub activity
            
        Returns:
            Activity ID
            
        Raises:
            HandlerError: If activity handling fails
        """
        try:
            # Store activity
            activity_id = await self.storage.create_activity(activity)
            
            # Get activity type
            activity_type = activity.get("type")
            if not activity_type:
                raise HandlerError("Activity has no type")
                
            # Get appropriate handler
            handler = self.handlers.get(activity_type)
            if not handler:
                raise HandlerError(f"No handler for activity type: {activity_type}")
                
            # Handle activity
            await handler.handle(activity)
            
            logger.info(f"Handled {activity_type} activity: {activity_id}")
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to handle activity: {e}")
            raise HandlerError(f"Failed to handle activity: {e}")
            
    async def handle_outbox(
        self,
        activity: Dict[str, Any],
        recipients: List[str]
    ) -> str:
        """
        Handle outgoing activity.
        
        Args:
            activity: ActivityPub activity
            recipients: List of recipient inbox URLs
            
        Returns:
            Activity ID
            
        Raises:
            DeliveryError: If delivery fails
        """
        try:
            # Store activity
            activity_id = await self.storage.create_activity(activity)
            
            # Deliver activity
            delivery_result = await self.delivery.deliver_activity(
                activity=activity,
                recipients=recipients
            )
            
            if delivery_result.failed:
                logger.warning(
                    f"Failed deliveries: {delivery_result.failed}"
                    f"\nError: {delivery_result.error_message}"
                )
                
            logger.info(
                f"Delivered activity {activity_id} to "
                f"{len(delivery_result.success)} recipients"
            )
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to handle outbox activity: {e}")
            raise DeliveryError(f"Failed to handle outbox activity: {e}")
            
    async def get_actor_inbox(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get actor's inbox contents."""
        return await self.storage.get_inbox(actor_id)
        
    async def get_actor_outbox(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get actor's outbox contents."""
        return await self.storage.get_outbox(actor_id)
        
    async def get_followers(self, actor_id: str) -> List[str]:
        """Get actor's followers."""
        return await self.storage.get_followers(actor_id)
        
    async def get_following(self, actor_id: str) -> List[str]:
        """Get actors that this actor is following."""
        return await self.storage.get_following(actor_id)
