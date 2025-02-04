"""
Update activity handler implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import ActivityHandler
from ..utils.exceptions import ValidationError, HandlerError
from ..models.activities import APUpdate

class UpdateHandler(ActivityHandler):
    """Handle Update activities."""

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Update activity."""
        try:
            # Validate basic structure
            if activity['type'] != 'Update':
                raise ValidationError("Invalid activity type")
            
            if 'object' not in activity:
                raise ValidationError("Missing object")
                
            if 'actor' not in activity:
                raise ValidationError("Missing actor")
            
            # Validate object exists
            obj = activity['object']
            if not isinstance(obj, dict) or 'id' not in obj:
                raise ValidationError("Invalid object format")
                
            existing = await self.storage.get_object(obj['id'])
            if not existing:
                raise ValidationError(f"Object not found: {obj['id']}")
            
            # Validate actor has permission
            if existing.get('attributedTo') != activity['actor']:
                raise ValidationError("Not authorized to update object")
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}")

    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """Process Update activity."""
        try:
            # Store update activity
            activity_id = await self.storage.create_activity(activity)
            
            # Update object
            obj = activity['object']
            obj['updated'] = datetime.utcnow().isoformat()
            
            # Preserve immutable fields
            existing = await self.storage.get_object(obj['id'])
            for field in ['id', 'type', 'attributedTo', 'published']:
                obj[field] = existing[field]
            
            # Store updated object
            await self.storage.update_object(obj['id'], obj)
            
            # Deliver update to recipients
            await self._deliver_update(activity)
            
            return activity_id
            
        except Exception as e:
            raise HandlerError(f"Failed to process Update: {e}")

    async def _deliver_update(self, activity: Dict[str, Any]) -> None:
        """Deliver update to recipients."""
        obj = activity['object']
        
        # Collect recipients
        recipients = []
        
        # Add mentioned users
        if 'tag' in obj:
            for tag in obj['tag']:
                if tag.get('type') == 'Mention':
                    recipients.append(tag['href'])
        
        # Add followers if public
        actor = await self.storage.get_object(activity['actor'])
        if actor and actor.get('followers'):
            if 'public' in obj.get('to', []):
                recipients.append(actor['followers'])
        
        # Deliver activity
        if recipients:
            await self.delivery.deliver_activity(
                activity=activity,
                recipients=recipients
            )