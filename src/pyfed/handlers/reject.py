"""
Handler for Reject activities.
"""

from typing import Dict, Any
from .base import ActivityHandler
from pyfed.utils.exceptions import HandlerError, ValidationError
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class RejectHandler(ActivityHandler):
    """Handles Reject activities."""

    REJECTABLE_TYPES = ['Follow']

    async def handle(self, activity: Dict[str, Any]) -> None:
        """Handle Reject activity."""
        try:
            await self.validate(activity)
            await self.pre_handle(activity)

            actor = activity.get('actor')
            object_data = activity.get('object')

            # Resolve object if it's a string ID
            if isinstance(object_data, str):
                resolved_object = await self.resolve_object_data(object_data)
                if not resolved_object:
                    raise HandlerError("Could not resolve activity")
                object_data = resolved_object

            # Verify authorization
            if object_data.get('object') != actor:
                raise HandlerError("Unauthorized: can only reject activities targeting self")

            # Handle based on rejected activity type
            if object_data.get('type') == 'Follow':
                # Check if follow request exists and hasn't been handled
                status = await self.storage.get_follow_request_status(
                    follower=object_data['actor'],
                    following=object_data['object']
                )
                
                if status == 'rejected':
                    raise HandlerError("Follow request already rejected")
                elif status == 'accepted':
                    raise HandlerError("Follow request already accepted")

                await self._handle_reject_follow(
                    follower=object_data['actor'],
                    following=object_data['object'],
                    reason=activity.get('content')
                )

            # Store reject activity
            activity_id = await self.storage.create_activity(activity)

            # Notify original actor
            if object_data.get('actor'):
                await self.delivery.deliver_activity(activity, [object_data['actor']])

            await self.post_handle(activity)
            logger.info(f"Handled Reject activity: {actor} -> {object_data.get('id')}")
            
        except ValidationError:
            raise
        except HandlerError:
            raise
        except Exception as e:
            logger.error(f"Failed to handle Reject activity: {e}")
            raise HandlerError(f"Failed to handle Reject activity: {e}")

    async def _handle_reject_follow(self, follower: str, following: str, reason: str = None) -> None:
        """Handle rejecting a Follow."""
        await self.storage.remove_follow_request(
            follower=follower,
            following=following,
            reason=reason
        )

    async def validate(self, activity: Dict[str, Any]) -> None:
        """Validate Reject activity."""
        if activity.get('type') != 'Reject':
            raise ValidationError("Invalid activity type")
        
        object_data = activity.get('object')
        if not object_data:
            raise ValidationError("Reject must have an object")
            
        if isinstance(object_data, dict):
            object_type = object_data.get('type')
            if object_type not in self.REJECTABLE_TYPES:
                raise ValidationError(f"Cannot reject activity type: {object_type}")