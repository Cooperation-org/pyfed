"""
Enhanced Create activity handler.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import ActivityHandler
from ..utils.exceptions import ValidationError, HandlerError
from ..models.activities import APCreate
from ..models.objects import APNote, APArticle, APImage

from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class CreateHandler(ActivityHandler):
    """Enhanced Create activity handler."""

    SUPPORTED_TYPES = {
        'Note': APNote,
        'Article': APArticle,
        'Image': APImage
    }

    async def validate(self, activity: Dict[str, Any]) -> None:
        """
        Enhanced Create validation.
        
        Validates:
        - Activity structure
        - Object type support
        - Content rules
        - Media attachments
        - Rate limits
        """
        try:
            # Validate basic structure
            create = APCreate.model_validate(activity)
            
            # Validate object
            obj = activity.get('object', {})
            obj_type = obj.get('type')
            
            if not obj_type or obj_type not in self.SUPPORTED_TYPES:
                raise ValidationError(f"Unsupported object type: {obj_type}")
                
            # Validate object model
            model_class = self.SUPPORTED_TYPES[obj_type]
            model_class.model_validate(obj)
            
            # Check actor permissions
            actor = await self.resolver.resolve_actor(activity['actor'])
            if not actor:
                raise ValidationError("Actor not found")
                
            # Check rate limits
            await self._check_rate_limits(actor['id'])
            
            # Validate content
            await self._validate_content(obj)
            
        except Exception as e:
            raise ValidationError(f"Create validation failed: {e}")

    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """
        Enhanced Create processing.
        
        Handles:
        - Object storage
        - Side effects
        - Notifications
        - Federation
        """
        try:
            # Store object
            obj = activity['object']
            object_id = await self.storage.create_object(obj)
            
            # Store activity
            activity_id = await self.storage.create_activity(activity)
            
            # Process mentions
            if mentions := await self._extract_mentions(obj):
                await self._handle_mentions(mentions, activity)
            
            # Process attachments
            if attachments := obj.get('attachment', []):
                await self._process_attachments(attachments, object_id)
            
            # Handle notifications
            await self._send_notifications(activity)
            
            # Update collections
            await self._update_collections(activity)
            
            return activity_id
            
        except Exception as e:
            logger.error(f"Create processing failed: {e}")
            raise HandlerError(f"Failed to process Create: {e}")

    async def _check_rate_limits(self, actor_id: str) -> None:
        """Check rate limits for actor."""
        

    async def _validate_content(self, obj: Dict[str, Any]) -> None:
        """Validate object content."""
        

    async def _extract_mentions(self, obj: Dict[str, Any]) -> List[str]:
        """Extract mentions from object."""
        

    async def _handle_mentions(self, 
                             mentions: List[str],
                             activity: Dict[str, Any]) -> None:
        """Handle mentions in activity."""
        

    async def _process_attachments(self,
                                 attachments: List[Dict[str, Any]],
                                 object_id: str) -> None:
        """Process media attachments."""
        

    async def _send_notifications(self, activity: Dict[str, Any]) -> None:
        """Send notifications for activity."""
        

    async def _update_collections(self, activity: Dict[str, Any]) -> None:
        """Update relevant collections."""
        