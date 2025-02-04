"""
ActivityPub federation protocol implementation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass

from ..storage.base import BaseStorageBackend
from ..federation.delivery import ActivityDelivery
from ..utils.exceptions import ProtocolError
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ProtocolConfig:
    """Protocol configuration."""
    auto_accept_follows: bool = False
    allow_public_posts: bool = True
    allow_public_replies: bool = True
    require_follow_for_dm: bool = True
    max_recipients: int = 100

class FederationProtocol:
    """ActivityPub federation protocol implementation."""
    
    def __init__(
        self,
        storage: BaseStorageBackend,
        delivery: ActivityDelivery,
        config: Optional[ProtocolConfig] = None
    ):
        self.storage = storage
        self.delivery = delivery
        self.config = config or ProtocolConfig()
        
    async def _create_response_activity(
        self,
        type: str,
        actor_id: str,
        in_response_to: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a response activity."""
        return {
            'type': type,
            'actor': actor_id,
            'object': in_response_to['id'],
            'to': [in_response_to['actor']],
            'published': datetime.utcnow().isoformat() + 'Z'
        }
        
    async def handle_follow(self, activity: Dict[str, Any]) -> None:
        """Handle Follow activity."""
        try:
            actor_id = activity['actor']
            object_id = activity['object']
            
            # Store follow request
            await self.storage.create_follow(
                follower=actor_id,
                following=object_id
            )
            
            if self.config.auto_accept_follows:
                # Create Accept activity
                accept = await self._create_response_activity(
                    'Accept',
                    object_id,
                    activity
                )
                
                # Store and deliver Accept
                await self.storage.create_activity(accept)
                await self.delivery.deliver_to_actor(accept, actor_id)
                
        except Exception as e:
            logger.error(f"Failed to handle Follow: {e}")
            raise ProtocolError(f"Follow handling failed: {e}")
            
    async def handle_like(self, activity: Dict[str, Any]) -> None:
        """Handle Like activity."""
        try:
            actor_id = activity['actor']
            object_id = activity['object']
            
            # Store like
            await self.storage.create_like(
                actor_id=actor_id,
                object_id=object_id
            )
            
            # Notify object owner
            object = await self.storage.get_object(object_id)
            if object and object.get('attributedTo'):
                notification = {
                    'type': 'Notification',
                    'actor': actor_id,
                    'object': activity,
                    'to': [object['attributedTo']]
                }
                await self.delivery.deliver_to_actor(
                    notification,
                    object['attributedTo']
                )
                
        except Exception as e:
            logger.error(f"Failed to handle Like: {e}")
            raise ProtocolError(f"Like handling failed: {e}")
            
    async def handle_announce(self, activity: Dict[str, Any]) -> None:
        """Handle Announce activity."""
        try:
            actor_id = activity['actor']
            object_id = activity['object']
            
            # Fetch and store announced object if not local
            object = await self.storage.get_object(object_id)
            if not object:
                # Fetch from remote
                object = await self.delivery.fetch_resource(object_id)
                await self.storage.create_object(object)
                
            # Store announce
            await self.storage.create_activity(activity)
            
            # Notify object owner
            if object.get('attributedTo'):
                notification = {
                    'type': 'Notification',
                    'actor': actor_id,
                    'object': activity,
                    'to': [object['attributedTo']]
                }
                await self.delivery.deliver_to_actor(
                    notification,
                    object['attributedTo']
                )
                
        except Exception as e:
            logger.error(f"Failed to handle Announce: {e}")
            raise ProtocolError(f"Announce handling failed: {e}")
            
    async def handle_create(self, activity: Dict[str, Any]) -> None:
        """Handle Create activity."""
        try:
            object = activity['object']
            
            # Validate object
            if not isinstance(object, dict):
                raise ProtocolError("Invalid object format")
                
            # Store object
            await self.storage.create_object(object)
            
            # Store activity
            await self.storage.create_activity(activity)
            
            # Handle mentions and tags
            await self._handle_mentions(activity)
            
        except Exception as e:
            logger.error(f"Failed to handle Create: {e}")
            raise ProtocolError(f"Create handling failed: {e}")
            
    async def _handle_mentions(self, activity: Dict[str, Any]) -> None:
        """Handle mentions in activity."""
        object = activity['object']
        if 'tag' in object:
            for tag in object['tag']:
                if tag.get('type') == 'Mention':
                    notification = {
                        'type': 'Notification',
                        'actor': activity['actor'],
                        'object': activity,
                        'to': [tag['href']]
                    }
                    await self.delivery.deliver_to_actor(
                        notification,
                        tag['href']
                    )
                    
    async def handle_delete(self, activity: Dict[str, Any]) -> None:
        """Handle Delete activity."""
        try:
            object_id = activity['object']
            if isinstance(object_id, dict):
                object_id = object_id['id']
                
            # Verify ownership
            object = await self.storage.get_object(object_id)
            if object and object.get('attributedTo') == activity['actor']:
                # Mark object as deleted
                await self.storage.delete_object(object_id)
                
                # Store delete activity
                await self.storage.create_activity(activity)
                
        except Exception as e:
            logger.error(f"Failed to handle Delete: {e}")
            raise ProtocolError(f"Delete handling failed: {e}")
            
    async def handle_update(self, activity: Dict[str, Any]) -> None:
        """Handle Update activity."""
        try:
            object = activity['object']
            if not isinstance(object, dict):
                raise ProtocolError("Invalid object format")
                
            # Verify ownership
            existing = await self.storage.get_object(object['id'])
            if existing and existing.get('attributedTo') == activity['actor']:
                # Update object
                await self.storage.update_object(object['id'], object)
                
                # Store update activity
                await self.storage.create_activity(activity)
                
        except Exception as e:
            logger.error(f"Failed to handle Update: {e}")
            raise ProtocolError(f"Update handling failed: {e}")
            
    async def handle_undo(self, activity: Dict[str, Any]) -> None:
        """Handle Undo activity."""
        try:
            object = activity['object']
            if isinstance(object, str):
                object = await self.storage.get_activity(object)
                
            if not object:
                raise ProtocolError("Object not found")
                
            # Verify ownership
            if object.get('actor') != activity['actor']:
                raise ProtocolError("Not authorized to undo this activity")
                
            # Handle based on object type
            if object['type'] == 'Follow':
                await self.storage.delete_follow(
                    follower=object['actor'],
                    following=object['object']
                )
                
            elif object['type'] == 'Like':
                await self.storage.delete_like(
                    actor_id=object['actor'],
                    object_id=object['object']
                )
                
            elif object['type'] == 'Announce':
                # Just store the undo activity
                await self.storage.create_activity(activity)
                
            else:
                logger.warning(f"Unhandled undo type: {object['type']}")
                
        except Exception as e:
            logger.error(f"Failed to handle Undo: {e}")
            raise ProtocolError(f"Undo handling failed: {e}")
            
    async def handle_accept(self, activity: Dict[str, Any]) -> None:
        """Handle Accept activity."""
        try:
            object = activity['object']
            if isinstance(object, str):
                object = await self.storage.get_activity(object)
                
            if not object or object['type'] != 'Follow':
                raise ProtocolError("Invalid Accept object")
                
            # Update follow status
            await self.storage.update_follow(
                follower=object['actor'],
                following=object['object'],
                accepted=True
            )
            
            # Store accept activity
            await self.storage.create_activity(activity)
            
        except Exception as e:
            logger.error(f"Failed to handle Accept: {e}")
            raise ProtocolError(f"Accept handling failed: {e}")
            
    async def handle_reject(self, activity: Dict[str, Any]) -> None:
        """Handle Reject activity."""
        try:
            object = activity['object']
            if isinstance(object, str):
                object = await self.storage.get_activity(object)
                
            if not object or object['type'] != 'Follow':
                raise ProtocolError("Invalid Reject object")
                
            # Delete follow request
            await self.storage.delete_follow(
                follower=object['actor'],
                following=object['object']
            )
            
            # Store reject activity
            await self.storage.create_activity(activity)
            
        except Exception as e:
            logger.error(f"Failed to handle Reject: {e}")
            raise ProtocolError(f"Reject handling failed: {e}")
            
    # Local activity handlers
    
    async def handle_local_create(self, activity: Dict[str, Any]) -> None:
        """Handle local Create activity."""
        await self.handle_create(activity)
        
    async def handle_local_follow(self, activity: Dict[str, Any]) -> None:
        """Handle local Follow activity."""
        # For local follows, we need to deliver the Follow activity
        # to the target actor and wait for Accept/Reject
        try:
            target_actor = activity['object']
            await self.delivery.deliver_to_actor(activity, target_actor)
            
        except Exception as e:
            logger.error(f"Failed to handle local Follow: {e}")
            raise ProtocolError(f"Local Follow handling failed: {e}")
            
    async def handle_local_like(self, activity: Dict[str, Any]) -> None:
        """Handle local Like activity."""
        await self.handle_like(activity)
        
    async def handle_local_announce(self, activity: Dict[str, Any]) -> None:
        """Handle local Announce activity."""
        await self.handle_announce(activity)
        
    async def handle_local_delete(self, activity: Dict[str, Any]) -> None:
        """Handle local Delete activity."""
        await self.handle_delete(activity)
        
    async def handle_local_update(self, activity: Dict[str, Any]) -> None:
        """Handle local Update activity."""
        await self.handle_update(activity)
        
    async def handle_local_undo(self, activity: Dict[str, Any]) -> None:
        """Handle local Undo activity."""
        await self.handle_undo(activity)
