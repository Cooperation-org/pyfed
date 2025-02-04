"""
Inbox handler for ActivityPub server.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
from dataclasses import dataclass

from ...storage.base import BaseStorageBackend
from ...federation.delivery import ActivityDelivery
from ...federation.protocol import FederationProtocol
from ...security.http_signatures import HTTPSignatureVerifier
from ...utils.exceptions import HandlerError, ValidationError
from ...utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class InboxRequest:
    """Inbox request data."""
    activity: Dict[str, Any]
    signature: Optional[Dict[str, str]] = None
    date: Optional[str] = None
    content_type: Optional[str] = None
    digest: Optional[str] = None

class InboxHandler:
    """Handle incoming activities in inbox."""
    
    def __init__(
        self,
        storage: BaseStorageBackend,
        delivery: ActivityDelivery,
        protocol: FederationProtocol,
        signature_verifier: HTTPSignatureVerifier
    ):
        self.storage = storage
        self.delivery = delivery
        self.protocol = protocol
        self.signature_verifier = signature_verifier
        
    async def validate_request(self, request: InboxRequest) -> None:
        """Validate incoming request."""
        if not request.activity:
            raise ValidationError("No activity provided")
            
        if not request.signature:
            raise ValidationError("No signature provided")
            
        if not request.date:
            raise ValidationError("No date header provided")
            
        if not request.content_type or 'application/activity+json' not in request.content_type:
            raise ValidationError("Invalid content type")
            
        # Verify signature
        if not await self.signature_verifier.verify(
            request.signature,
            request.activity,
            request.date
        ):
            raise ValidationError("Invalid signature")
            
        # Validate activity format
        if not self._validate_activity_format(request.activity):
            raise ValidationError("Invalid activity format")
            
    def _validate_activity_format(self, activity: Dict[str, Any]) -> bool:
        """Validate activity format."""
        required_fields = ['type', 'actor', 'id']
        return all(field in activity for field in required_fields)
        
    async def process_activity(self, request: InboxRequest) -> None:
        """Process incoming activity."""
        try:
            # Store activity
            await self.storage.create_activity(request.activity)
            
            # Process based on activity type
            activity_type = request.activity['type']
            
            if activity_type == 'Follow':
                await self.protocol.handle_follow(request.activity)
                
            elif activity_type == 'Like':
                await self.protocol.handle_like(request.activity)
                
            elif activity_type == 'Announce':
                await self.protocol.handle_announce(request.activity)
                
            elif activity_type == 'Create':
                await self.protocol.handle_create(request.activity)
                
            elif activity_type == 'Delete':
                await self.protocol.handle_delete(request.activity)
                
            elif activity_type == 'Update':
                await self.protocol.handle_update(request.activity)
                
            elif activity_type == 'Undo':
                await self.protocol.handle_undo(request.activity)
                
            elif activity_type == 'Accept':
                await self.protocol.handle_accept(request.activity)
                
            elif activity_type == 'Reject':
                await self.protocol.handle_reject(request.activity)
                
            else:
                logger.warning(f"Unhandled activity type: {activity_type}")
                
        except Exception as e:
            logger.error(f"Failed to process activity: {e}")
            raise HandlerError(f"Activity processing failed: {e}")
            
    async def handle_request(self, request: InboxRequest) -> None:
        """Handle inbox request."""
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
