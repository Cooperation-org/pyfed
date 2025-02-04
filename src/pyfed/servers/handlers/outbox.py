"""
Outbox handler for ActivityPub server.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import json
import logging
from dataclasses import dataclass

from ...storage.base import BaseStorageBackend
from ...federation.delivery import ActivityDelivery
from ...federation.protocol import FederationProtocol
from ...security.key_management import KeyManager
from ...utils.exceptions import HandlerError, ValidationError
from ...utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class OutboxRequest:
    """Outbox request data."""
    activity: Dict[str, Any]
    actor_id: str
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    bto: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class OutboxHandler:
    """Handle outgoing activities from outbox."""
    
    def __init__(
        self,
        storage: BaseStorageBackend,
        delivery: ActivityDelivery,
        protocol: FederationProtocol,
        key_manager: KeyManager
    ):
        self.storage = storage
        self.delivery = delivery
        self.protocol = protocol
        self.key_manager = key_manager
        
    def _get_recipients(self, request: OutboxRequest) -> Set[str]:
        """Get unique recipients for activity."""
        recipients = set()
        
        # Add public recipients
        for field in [request.to, request.cc]:
            if field:
                recipients.update(
                    addr for addr in field
                    if addr != 'https://www.w3.org/ns/activitystreams#Public'
                )
                
        # Add private recipients
        for field in [request.bto, request.bcc]:
            if field:
                recipients.update(field)
                
        return recipients
        
    async def _prepare_activity(self, request: OutboxRequest) -> Dict[str, Any]:
        """Prepare activity for delivery."""
        activity = request.activity.copy()
        
        # Add actor if not present
        if 'actor' not in activity:
            activity['actor'] = request.actor_id
            
        # Add published date
        if 'published' not in activity:
            activity['published'] = datetime.utcnow().isoformat() + 'Z'
            
        # Sign activity
        key_id = f"{request.actor_id}#main-key"
        signature = await self.key_manager.sign(
            activity,
            key_id=key_id
        )
        activity['signature'] = signature
        
        return activity
        
    async def validate_request(self, request: OutboxRequest) -> None:
        """Validate outbox request."""
        if not request.activity:
            raise ValidationError("No activity provided")
            
        if not request.actor_id:
            raise ValidationError("No actor ID provided")
            
        # Validate activity format
        if not self._validate_activity_format(request.activity):
            raise ValidationError("Invalid activity format")
            
        # Validate actor exists
        actor = await self.storage.get_actor(request.actor_id)
        if not actor:
            raise ValidationError("Actor not found")
            
    def _validate_activity_format(self, activity: Dict[str, Any]) -> bool:
        """Validate activity format."""
        required_fields = ['type', 'id']
        return all(field in activity for field in required_fields)
        
    async def process_activity(self, request: OutboxRequest) -> None:
        """Process outgoing activity."""
        try:
            # Prepare activity
            activity = await self._prepare_activity(request)
            
            # Store activity
            await self.storage.create_activity(activity)
            
            # Get recipients
            recipients = self._get_recipients(request)
            
            if recipients:
                # Group recipients by shared inbox
                await self.delivery.deliver_to_shared_inbox(activity, list(recipients))
                
            # Process based on activity type
            activity_type = activity['type']
            
            if activity_type == 'Create':
                await self.protocol.handle_local_create(activity)
                
            elif activity_type == 'Follow':
                await self.protocol.handle_local_follow(activity)
                
            elif activity_type == 'Like':
                await self.protocol.handle_local_like(activity)
                
            elif activity_type == 'Announce':
                await self.protocol.handle_local_announce(activity)
                
            elif activity_type == 'Delete':
                await self.protocol.handle_local_delete(activity)
                
            elif activity_type == 'Update':
                await self.protocol.handle_local_update(activity)
                
            elif activity_type == 'Undo':
                await self.protocol.handle_local_undo(activity)
                
            else:
                logger.warning(f"Unhandled activity type: {activity_type}")
                
        except Exception as e:
            logger.error(f"Failed to process activity: {e}")
            raise HandlerError(f"Activity processing failed: {e}")
            
    async def handle_request(self, request: OutboxRequest) -> None:
        """Handle outbox request."""
        try:
            # Validate request
            await self.validate_request(request)
            
            # Process activity
            await self.process_activity(request)
            
        except ValidationError as e:
            logger.error(f"Invalid request: {e}")
            raise HandlerError(f"Invalid request: {e}")
            
        except Exception as e:
            logger.error(f"Failed to handle request: {e}")
            raise HandlerError(f"Request handling failed: {e}")
