"""Like activity handler."""

from typing import Dict, Any
from .base import ActivityHandler
from pyfed.utils.exceptions import HandlerError, ValidationError
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class LikeHandler(ActivityHandler):
    """Handles Like activities."""

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Like activity."""
        if activity.get('type') != 'Like':
            raise ValidationError("Invalid activity type")
        
        if not activity.get('actor'):
            raise ValidationError("Like must have an actor")
            
        if not activity.get('object'):
            raise ValidationError("Like must have an object")

    async def process(self, activity: Dict[str, Any]) -> None:
        """Handle Like activity."""
        try:
            await self.validate(activity)
            await self.pre_handle(activity)

            actor = activity.get('actor')
            object_id = activity.get('object')

            # Resolve target object
            object_data = await self.resolve_object_data(object_id)
            if not object_data:
                raise HandlerError(f"Could not resolve object: {object_id}")

            # Check for duplicate like
            if await self.storage.has_liked(actor, object_id):
                raise HandlerError("Already liked this object")

            # Store like
            await self.storage.create_like(
                actor=actor,
                object_id=object_id
            )

            # Store like activity
            activity_id = await self.storage.create_activity(activity)

            # Notify object creator
            await self._notify_object_owner(object_data, activity)

            await self.post_handle(activity)
            logger.info(f"Handled Like activity: {actor} -> {object_id}")
            
        except ValidationError:
            raise
        except HandlerError:
            raise
        except Exception as e:
            logger.error(f"Failed to handle Like activity: {e}")
            raise HandlerError(f"Failed to handle Like activity: {e}")

    async def _notify_object_owner(self, object_data: Dict[str, Any], activity: Dict[str, Any]) -> None:
        """Notify object owner about the like."""
        if object_data.get('attributedTo'):
            target_actor = await self.resolver.resolve_actor(
                object_data['attributedTo']
            )
            if target_actor and target_actor.get('inbox'):
                await self.delivery.deliver_activity(
                    activity=activity,
                    recipients=[target_actor['inbox']]
                )

