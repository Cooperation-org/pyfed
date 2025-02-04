"""
federation/resolver.py
ActivityPub resolver implementation.
"""

from typing import Dict, Any, Optional
import aiohttp
from urllib.parse import urlparse

from ..utils.exceptions import ResolverError
from ..utils.logging import get_logger
from ..cache.actor_cache import ActorCache
from .webfinger import WebFingerClient

logger = get_logger(__name__)

class ActivityPubResolver:
    """Resolves ActivityPub resources."""

    def __init__(self, 
                 actor_cache: Optional[ActorCache] = None,
                 discovery_service: Optional[WebFingerClient] = None):
        """
        Initialize resolver.
        
        Args:
            actor_cache: Optional actor cache
            discovery_service: Optional WebFinger service
        """
        self.actor_cache = actor_cache
        self.discovery_service = discovery_service

    async def resolve_actor(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an actor by ID or account.
        
        Args:
            actor_id: Actor ID or account (user@domain)
            
        Returns:
            Actor data or None if not found
        """
        try:
            # Check cache first
            if self.actor_cache:
                cached = await self.actor_cache.get(actor_id)
                if cached:
                    return cached

            # Try WebFinger if it's an account
            if '@' in actor_id and self.discovery_service:
                actor_url = await self.discovery_service.get_actor_url(actor_id)
                if actor_url:
                    actor_id = actor_url

            # Fetch actor data
            headers = {
                "Accept": "application/activity+json",
                "User-Agent": "PyFed/1.0"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(actor_id, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch actor {actor_id}: {response.status}"
                        )
                        return None

                    actor_data = await response.json()

                    # Cache the result
                    if self.actor_cache:
                        await self.actor_cache.set(actor_id, actor_data)

                    return actor_data

        except Exception as e:
            logger.error(f"Failed to resolve actor {actor_id}: {e}")
            return None

    async def resolve_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an object by ID.
        
        Args:
            object_id: Object ID
            
        Returns:
            Object data or None if not found
        """
        try:
            headers = {
                "Accept": "application/activity+json",
                "User-Agent": "PyFed/1.0"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(object_id, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch object {object_id}: {response.status}"
                        )
                        return None

                    return await response.json()

        except Exception as e:
            logger.error(f"Failed to resolve object {object_id}: {e}")
            return None

    async def resolve_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an activity by ID.
        
        Args:
            activity_id: Activity ID
            
        Returns:
            Activity data or None if not found
        """
        return await self.resolve_object(activity_id)