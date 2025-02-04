"""
Delete activity handler implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import ActivityHandler
# from ..monitoring.decorators import monitor, trace_async
from ..utils.exceptions import ValidationError, HandlerError
from ..models.activities import APDelete

class DeleteHandler(ActivityHandler):
    """Handle Delete activities."""

    # @monitor("handler.delete.validate")
    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Delete activity."""
        try:
            # Validate basic structure
            delete = APDelete.model_validate(activity)
            
            # Verify actor permissions
            actor = await self.resolver.resolve_actor(activity['actor'])
            if not actor:
                raise ValidationError("Actor not found")
                
            # Verify object ownership
            object_id = activity.get('object')
            if isinstance(object_id, dict):
                object_id = object_id.get('id')
                
            stored_object = await self.storage.get_object(object_id)
            if not stored_object:
                raise ValidationError("Object not found")
                
            if stored_object.get('attributedTo') != activity['actor']:
                raise ValidationError("Not authorized to delete this object")
                
        except Exception as e:
            raise ValidationError(f"Delete validation failed: {e}")

    # @monitor("handler.delete.process")
    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """Process Delete activity."""
        try:
            # Store delete activity
            activity_id = await self.storage.create_activity(activity)
            
            # Delete object
            object_id = activity.get('object')
            if isinstance(object_id, dict):
                object_id = object_id.get('id')
                
            await self.storage.delete_object(object_id)
            
            # Handle tombstone
            await self._create_tombstone(object_id)
            
            # Update collections
            await self._update_collections(object_id)
            
            return activity_id
            
        except Exception as e:
            raise HandlerError(f"Failed to process Delete: {e}")

    async def _create_tombstone(self, object_id: str) -> None:
        """Create tombstone for deleted object."""
        tombstone = {
            'type': 'Tombstone',
            'id': object_id,
            'deleted': datetime.utcnow().isoformat()
        }
        await self.storage.create_object(tombstone)

    async def _update_collections(self, object_id: str) -> None:
        """Update collections after deletion."""
        
            