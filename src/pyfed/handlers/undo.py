"""
Undo activity handler implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import ActivityHandler
from ..utils.exceptions import ValidationError, HandlerError
from ..models.activities import APUndo

class UndoHandler(ActivityHandler):
    """Handle Undo activities."""

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Undo activity."""
        try:
            # Validate basic structure
            if activity['type'] != 'Undo':
                raise ValidationError("Invalid activity type")
            
            if 'object' not in activity:
                raise ValidationError("Missing object")
                
            if 'actor' not in activity:
                raise ValidationError("Missing actor")
            
            # Validate object exists
            obj = activity['object']
            if isinstance(obj, str):
                obj = await self.storage.get_activity(obj)
                if not obj:
                    raise ValidationError(f"Activity not found: {activity['object']}")
            
            # Validate actor has permission
            if obj.get('actor') != activity['actor']:
                raise ValidationError("Not authorized to undo activity")
                
            # Validate activity can be undone
            if obj['type'] not in ['Like', 'Announce', 'Follow', 'Block']:
                raise ValidationError(f"Cannot undo activity type: {obj['type']}")
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}")

    async def process(self, activity: Dict[str, Any]) -> Optional[str]:
        """Process Undo activity."""
        try:
            # Store undo activity
            activity_id = await self.storage.create_activity(activity)
            
            # Get original activity
            obj = activity['object']
            if isinstance(obj, str):
                obj = await self.storage.get_activity(obj)
            
            # Process based on activity type
            if obj['type'] == 'Like':
                await self._undo_like(obj)
            elif obj['type'] == 'Announce':
                await self._undo_announce(obj)
            elif obj['type'] == 'Follow':
                await self._undo_follow(obj)
            elif obj['type'] == 'Block':
                await self._undo_block(obj)
            
            # Deliver undo to recipients
            await self._deliver_undo(activity)
            
            return activity_id
            
        except Exception as e:
            raise HandlerError(f"Failed to process Undo: {e}")

    async def _undo_like(self, activity: Dict[str, Any]) -> None:
        """Undo a Like activity."""
        object_id = activity['object']
        actor = activity['actor']
        
        obj = await self.storage.get_object(object_id)
        if obj:
            likes = obj.get('likes', [])
            if actor in likes:
                likes.remove(actor)
                obj['likes'] = likes
                await self.storage.update_object(object_id, obj)

    async def _undo_announce(self, activity: Dict[str, Any]) -> None:
        """Undo an Announce activity."""
        object_id = activity['object']
        actor = activity['actor']
        
        obj = await self.storage.get_object(object_id)
        if obj:
            shares = obj.get('shares', [])
            if actor in shares:
                shares.remove(actor)
                obj['shares'] = shares
                await self.storage.update_object(object_id, obj)

    async def _undo_follow(self, activity: Dict[str, Any]) -> None:
        """Undo a Follow activity."""
        object_id = activity['object']
        actor = activity['actor']
        
        # Remove from following collection
        actor_obj = await self.storage.get_object(actor)
        if actor_obj:
            following = actor_obj.get('following', [])
            if object_id in following:
                following.remove(object_id)
                actor_obj['following'] = following
                await self.storage.update_object(actor, actor_obj)
        
        # Remove from followers collection
        target = await self.storage.get_object(object_id)
        if target:
            followers = target.get('followers', [])
            if actor in followers:
                followers.remove(actor)
                target['followers'] = followers
                await self.storage.update_object(object_id, target)

    async def _undo_block(self, activity: Dict[str, Any]) -> None:
        """Undo a Block activity."""
        object_id = activity['object']
        actor = activity['actor']
        
        actor_obj = await self.storage.get_object(actor)
        if actor_obj:
            blocks = actor_obj.get('blocks', [])
            if object_id in blocks:
                blocks.remove(object_id)
                actor_obj['blocks'] = blocks
                await self.storage.update_object(actor, actor_obj)

    async def _deliver_undo(self, activity: Dict[str, Any]) -> None:
        """Deliver undo to recipients."""
        obj = activity['object']
        if isinstance(obj, str):
            obj = await self.storage.get_activity(obj)
        
        # Deliver to original recipients
        if obj and obj.get('to'):
            await self.delivery.deliver_activity(
                activity=activity,
                recipients=obj['to']
            )