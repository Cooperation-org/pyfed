"""
Handler for Follow activities.
"""

from typing import Dict, Any
from .base import ActivityHandler
from pyfed.utils.exceptions import HandlerError, ValidationError
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class FollowHandler(ActivityHandler):
    """Handles Follow activities."""

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Follow activity."""
        if activity.get('type') != 'Follow':
            raise ValidationError("Invalid activity type")
        
        if not activity.get('actor'):
            raise ValidationError("Follow must have an actor")
            
        if not activity.get('object'):
            raise ValidationError("Follow must have an object")

    async def process(self, activity: Dict[str, Any]) -> None:
        """Handle Follow activity."""
        try:
            await self.validate(activity)
            # await self.pre_handle(activity)

            actor = activity.get('actor')
            target = activity.get('object')

            # Resolve target actor
            target_actor = await self.resolver.resolve_actor(target)
            if not target_actor:
                raise HandlerError(f"Could not resolve target actor: {target}")

            # Check if already following
            if await self.storage.is_following(actor, target):
                raise HandlerError("Already following this actor")

            # Store follow request
            await self.storage.create_follow_request(
                follower=actor,
                following=target
            )

            # Store follow activity
            activity_id = await self.storage.create_activity(activity)

            # Deliver to target's inbox
            target_inbox = target_actor.get('inbox')
            if not target_inbox:
                raise HandlerError("Target actor has no inbox")

            await self.delivery.deliver_activity(
                activity=activity,
                recipients=[target_inbox]
            )

            # await self.post_handle(activity)
            logger.info(f"Handled Follow activity: {actor} -> {target}")
            
        except ValidationError:
            raise
        except HandlerError:
            raise
        except Exception as e:
            logger.error(f"Failed to handle Follow activity: {e}")
            raise HandlerError(f"Failed to handle Follow activity: {e}")