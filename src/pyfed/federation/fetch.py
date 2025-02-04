"""
federation/fetch.py
Remote resource fetching implementation.
"""

from typing import Dict, Any, Optional, Union
import aiohttp
from urllib.parse import urlparse

from pyfed.security.http_signatures import HTTPSignatureVerifier
from pyfed.cache.actor_cache import ActorCache
from pyfed.utils.exceptions import FetchError
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class ResourceFetcher:
    """
    Handles fetching remote ActivityPub resources.
    
    This class:
    - Fetches remote actors and objects
    - Handles HTTP signatures
    - Uses caching when possible
    - Validates responses
    """
    
    def __init__(self,
                 signature_verifier: HTTPSignatureVerifier,
                 actor_cache: Optional[ActorCache] = None,
                 timeout: int = 30):
        """
        Initialize resource fetcher.
        
        Args:
            signature_verifier: HTTP signature verifier
            actor_cache: Optional actor cache
            timeout: Request timeout in seconds
        """
        self.signature_verifier = signature_verifier
        self.actor_cache = actor_cache
        self.timeout = timeout

    async def fetch_resource(self, url: str) -> Dict[str, Any]:
        """
        Fetch a remote resource.
        
        Args:
            url: Resource URL
            
        Returns:
            Resource data
            
        Raises:
            FetchError: If fetch fails
        """
        try:
            # Check actor cache first
            if self.actor_cache:
                cached = await self.actor_cache.get(url)
                if cached:
                    return cached

            # Sign request
            headers = await self.signature_verifier.sign_request(
                method='GET',
                path=urlparse(url).path,
                host=urlparse(url).netloc
            )
            headers['Accept'] = 'application/activity+json'

            # Fetch resource
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise FetchError(f"Failed to fetch {url}: {response.status}")
                        
                    data = await response.json()
                    
                    # Cache actor data
                    if self.actor_cache and data.get('type') in ('Person', 'Group', 'Organization', 'Service'):
                        await self.actor_cache.set(url, data)
                        
                    return data

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise FetchError(f"Failed to fetch {url}: {e}") 