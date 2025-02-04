"""
Announce activity handler implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import ActivityHandler
from ..utils.exceptions import ValidationError, HandlerError
from ..models.activities import APAnnounce

class AnnounceHandler(ActivityHandler):
    """Handle Announce (Boost/Reblog) activities."""

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Announce activity."""
        try:
            # Validate basic structure
            if activity['type'] != 'Announce':
                raise ValidationError("Invalid activity type")
            
            if 'object' not in activity:
                raise ValidationError("Missing object")
                
            if 'actor' not in activity:
                raise ValidationError("Missing actor")
            
            # Validate object exists
            object_id = activity['object']
            obj = await self.resolver.resolve_object(object_id)
            if not obj:
                raise ValidationError(f"Object not found: {object_id}")
            
            # Validate actor can announce
            actor = await self.resolver.resolve_actor(activity['actor'])
            if not actor:
                raise ValidationError(f"Actor not found: {activity['actor']}")
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}")

    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """Process Announce activity."""
        try:
            # Store announce activity
            activity_id = await self.storage.create_activity(activity)
            
            # Update object shares collection
            object_id = activity['object']
            await self._update_shares_collection(object_id, activity['actor'])
            
            # Update actor's shares collection
            await self._update_actor_shares(activity['actor'], object_id)
            
            # Send notifications
            await self._notify_object_owner(object_id, activity)
            
            # Deliver to followers
            await self._deliver_to_followers(activity)
            
            return activity_id
            
        except Exception as e:
            raise HandlerError(f"Failed to process Announce: {e}")

    async def _update_shares_collection(self, object_id: str, actor: str) -> None:
        """Update object's shares collection."""
        obj = await self.storage.get_object(object_id)
        if obj:
            shares = obj.get('shares', [])
            if actor not in shares:
                shares.append(actor)
                obj['shares'] = shares
                await self.storage.update_object(object_id, obj)

    async def _update_actor_shares(self, actor_id: str, object_id: str) -> None:
        """Update actor's shares collection."""
        actor = await self.storage.get_object(actor_id)
        if actor:
            shares = actor.get('shares', [])
            if object_id not in shares:
                shares.append(object_id)
                actor['shares'] = shares
                await self.storage.update_object(actor_id, actor)

    async def _notify_object_owner(self, object_id: str, activity: Dict[str, Any]) -> None:
        """Notify object owner about announce."""
        obj = await self.storage.get_object(object_id)
        if obj and obj.get('attributedTo'):
            # Implementation for notification
            pass

    async def _deliver_to_followers(self, activity: Dict[str, Any]) -> None:
        """Deliver announce to followers."""
        actor = await self.storage.get_object(activity['actor'])
        if actor and actor.get('followers'):
            await self.delivery.deliver_activity(
                activity=activity,
                recipients=[actor['followers']]
            )