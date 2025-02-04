"""Accept activity handler."""

from typing import Dict, Any
from .base import ActivityHandler
from pyfed.utils.exceptions import HandlerError, ValidationError
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class AcceptHandler(ActivityHandler):
    """Handles Accept activities."""

    ACCEPTABLE_TYPES = ['Follow']

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Accept activity."""
        if activity.get('type') != 'Accept':
            raise ValidationError("Invalid activity type")
        
        object_data = activity.get('object')
        if not object_data:
            raise ValidationError("Accept must have an object")
            
        # Check if object is a dict with type
        if isinstance(object_data, dict):
            object_type = object_data.get('type')
            if object_type not in self.ACCEPTABLE_TYPES:
                raise ValidationError(f"Cannot accept activity type: {object_type}")

    async def process(self, activity: Dict[str, Any]) -> None:
        """Handle Accept activity."""
        try:
            await self.validate(activity)
            # await self.pre_handle(activity)

            actor = activity.get('actor')
            object_data = activity.get('object')

            # Resolve object if it's a string ID
            if isinstance(object_data, str):
                try:
                    resolved_object = await self.resolve_object_data(object_data)
                    object_data = resolved_object
                except HandlerError:
                    raise HandlerError("Could not resolve Follow activity")

            # Verify it's a Follow activity
            if not isinstance(object_data, dict) or object_data.get('type') != 'Follow':
                raise HandlerError("Invalid Follow activity format")

            # Verify authorization
            if object_data.get('object') != actor:
                raise HandlerError("Unauthorized: can only accept activities targeting self")

            # Handle Follow acceptance
            await self._handle_accept_follow(
                follower=object_data['actor'],
                following=object_data['object']
            )

            # Store accept activity
            activity_id = await self.storage.create_activity(activity)

            # Notify original actor
            if object_data.get('actor'):
                await self.delivery.deliver_activity(activity, [object_data['actor']])

            # await self.post_handle(activity)
            
        except ValidationError:
            raise
        except HandlerError:
            raise
        except Exception as e:
            logger.error(f"Failed to handle Accept activity: {e}")
            raise HandlerError(f"Failed to handle Accept activity: {e}")

    async def _handle_accept_follow(self, follower: str, following: str) -> None:
        """Handle accepting a Follow."""
        await self.storage.confirm_follow(
            follower=follower,
            following=following
        )