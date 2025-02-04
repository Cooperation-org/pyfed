"""
federation/delivery.py
Activity delivery implementation with shared inbox optimization.
"""

from typing import Dict, Any, Optional, List, Set
from urllib.parse import urlparse
import aiohttp
from dataclasses import dataclass
from datetime import datetime
import asyncio
import certifi
import ssl
import json
from collections import defaultdict

from ..utils.exceptions import DeliveryError
from ..utils.logging import get_logger
from ..security.key_management import KeyManager
from ..security.http_signatures import HTTPSignatureVerifier
from ..federation.discovery import InstanceDiscovery
from ..federation.rate_limit import RateLimiter, RateLimit
from ..serializers.json_serializer import ActivityPubSerializer

logger = get_logger(__name__)

@dataclass
class DeliveryResult:
    """Delivery result."""
    success: List[str] = None
    failed: List[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_after: Optional[int] = None
    
    def __post_init__(self):
        self.success = self.success or []
        self.failed = self.failed or []

class ActivityDelivery:
    """Activity delivery implementation with shared inbox optimization."""
    
    def __init__(
        self,
        key_manager: KeyManager,
        discovery: InstanceDiscovery,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 20,
        max_concurrent: int = 10
    ):
        """Initialize delivery service."""
        self.key_manager = key_manager
        self.discovery = discovery
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_concurrent = max_concurrent
        self.session = None
        
        # Initialize HTTP signature verifier
        self.signature_verifier = HTTPSignatureVerifier(key_manager=key_manager)
        
        # Initialize rate limiter with default limits
        self.rate_limiter = RateLimiter(
            default_limit=RateLimit(
                requests=100,
                period=60,  # 100 requests per minute
                burst=20
            )
        )
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
        
    async def deliver_to_inbox(
        self,
        activity: Dict[str, Any],
        inbox_url: str,
        username: Optional[str] = None,
        retry_count: int = 0
    ) -> DeliveryResult:
        """Deliver activity to an inbox."""
        parsed_url = urlparse(inbox_url)
        domain = parsed_url.netloc
        result = DeliveryResult()
        
        try:
            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(domain):
                wait_time = await self.rate_limiter.get_wait_time(domain)
                await asyncio.sleep(wait_time)
            
            # Prepare headers with host
            headers = {
                'Content-Type': 'application/activity+json',
                'User-Agent': 'PyFed/1.0',
                'Accept': 'application/activity+json',
                'Host': domain  # Add host header required for signature
            }
            
            # Sign request using HTTPSignatureVerifier
            signed_headers = await self.signature_verifier.sign_request(
                method='POST',
                path=parsed_url.path,
                headers=headers,
                body=activity,  # Pass original dict for digest calculation
                username=username  # Pass username for key ID
            )
            
            # Use standardized JSON serialization
            body_json = ActivityPubSerializer.to_json_string(activity)
            
            # Make request with pre-serialized JSON
            session = await self._get_session()
            async with session.post(
                inbox_url,
                data=body_json,  # Use pre-serialized JSON
                headers=signed_headers,  # Use signed headers directly
                timeout=self.timeout
            ) as response:
                # Update rate limit state
                await self.rate_limiter.update_rate_limit(
                    domain,
                    response.headers
                )
                
                if response.status in (200, 201, 202):  
                    result.success.append(inbox_url)
                    result.status_code = response.status
                    return result
                    
                if response.status == 429 or (
                    response.status >= 500 and retry_count < self.max_retries
                ):
                    # Calculate retry delay
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    await asyncio.sleep(retry_after)
                    
                    # Retry delivery
                    return await self.deliver_to_inbox(
                        activity=activity,
                        inbox_url=inbox_url,
                        username=username,
                        retry_count=retry_count + 1
                    )
                    
                result.failed.append(inbox_url)
                result.status_code = response.status
                result.error_message = await response.text()
                
        except asyncio.TimeoutError:
            result.failed.append(inbox_url)
            result.error_message = "Delivery timeout"
            
        except Exception as e:
            result.failed.append(inbox_url)
            result.error_message = str(e)
            
        return result
        
    async def deliver_to_shared_inbox(
        self,
        activity: Dict[str, Any],
        recipients: List[str]
    ) -> DeliveryResult:
        """Deliver activity to shared inboxes."""
        result = DeliveryResult()
        
        try:
            # Group recipients by domain
            domain_inboxes = defaultdict(set)
            for recipient in recipients:
                domain = urlparse(recipient).netloc
                instance_info = await self.discovery.get_instance_info(domain)
                
                if instance_info and instance_info.shared_inbox:
                    domain_inboxes[domain].add(instance_info.shared_inbox)
                else:
                    # Fall back to personal inbox
                    actor = await self.discovery.get_actor(recipient)
                    if actor and actor.get('inbox'):
                        domain_inboxes[domain].add(actor['inbox'])
                        
            # Deliver to each shared inbox concurrently
            tasks = []
            for domain, inboxes in domain_inboxes.items():
                for inbox in inboxes:
                    task = self.deliver_to_inbox(activity, inbox)
                    tasks.append(task)
                    
                    # Limit concurrent deliveries
                    if len(tasks) >= self.max_concurrent:
                        delivery_results = await asyncio.gather(*tasks, return_exceptions=True)
                        for dr in delivery_results:
                            if isinstance(dr, DeliveryResult):
                                result.success.extend(dr.success)
                                result.failed.extend(dr.failed)
                        tasks = []
                        
            # Handle remaining tasks
            if tasks:
                delivery_results = await asyncio.gather(*tasks, return_exceptions=True)
                for dr in delivery_results:
                    if isinstance(dr, DeliveryResult):
                        result.success.extend(dr.success)
                        result.failed.extend(dr.failed)
                        
        except Exception as e:
            logger.error(f"Failed to deliver to shared inboxes: {e}")
            result.error_message = str(e)
            
        return result
        
    async def deliver_to_actor(
        self,
        activity: Dict[str, Any],
        actor_id: str
    ) -> DeliveryResult:
        """Deliver activity to an actor's inbox."""
        try:
            actor = await self.discovery.get_actor(actor_id)
            if not actor or 'inbox' not in actor:
                raise DeliveryError(f"Actor {actor_id} not found or has no inbox")
                
            return await self.deliver_to_inbox(activity, actor['inbox'])
            
        except Exception as e:
            logger.error(f"Failed to deliver to actor {actor_id}: {e}")
            return DeliveryResult(
                failed=[actor_id],
                error_message=str(e)
            )
            
    async def fetch_resource(self, url: str) -> Dict[str, Any]:
        """Fetch a remote resource."""
        try:
            headers = {
                'Accept': 'application/activity+json',
                'User-Agent': 'PyFed/1.0'
            }
            
            session = await self._get_session()
            async with session.get(
                url,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise DeliveryError(
                        f"Failed to fetch resource: {response.status}"
                    )
                    
        except Exception as e:
            raise DeliveryError(f"Failed to fetch resource: {e}")
            
    async def close(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()