"""
federation/discovery.py
Federation instance discovery implementation.

Handles:
- Instance metadata discovery
- WebFinger resolution
- NodeInfo discovery
- Actor discovery
"""

from typing import Dict, Any, Optional, List
import aiohttp
import json
from urllib.parse import urlparse, urljoin
from datetime import datetime
import asyncio
from dataclasses import dataclass
import certifi
import ssl

from ..utils.exceptions import DiscoveryError
from ..utils.logging import get_logger
from ..cache.memory_cache import MemoryCache

logger = get_logger(__name__)

@dataclass
class NodeInfo:
    """NodeInfo data."""
    version: str
    software: Dict[str, str]
    protocols: List[str]
    services: Dict[str, List[str]]
    usage: Dict[str, Any]
    open_registrations: bool
    metadata: Dict[str, Any]

@dataclass
class InstanceInfo:
    """Instance information."""
    domain: str
    nodeinfo: Optional[NodeInfo]
    software_version: Optional[str]
    instance_actor: Optional[Dict[str, Any]]
    shared_inbox: Optional[str]
    endpoints: Dict[str, str]
    features: Dict[str, bool]
    last_updated: datetime

class InstanceDiscovery:
    """Federation instance discovery."""

    def __init__(self,
                 cache_ttl: int = 3600,  # 1 hour
                 request_timeout: int = 10):
        """Initialize instance discovery."""
        self.cache = MemoryCache(ttl=cache_ttl)
        self.timeout = request_timeout
        self.session = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "User-Agent": "PyFed/1.0",
                "Accept": "application/activity+json"
            },
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )

    async def discover_instance(self, domain: str) -> InstanceInfo:
        """
        Discover instance information.
        
        Args:
            domain: Instance domain
            
        Returns:
            InstanceInfo with complete instance data
        """
        try:
            # Check cache first
            cache_key = f"instance:{domain}"
            if cached := await self.cache.get(cache_key):
                return cached

            # Discover instance components
            nodeinfo = await self.discover_nodeinfo(domain)
            instance_actor = await self.discover_instance_actor(domain)
            endpoints = await self.discover_endpoints(domain)
            features = await self.discover_features(domain)

            # Build instance info
            info = InstanceInfo(
                domain=domain,
                nodeinfo=nodeinfo,
                software_version=nodeinfo.software.get('version') if nodeinfo else None,
                instance_actor=instance_actor,
                shared_inbox=instance_actor.get('endpoints', {}).get('sharedInbox')
                    if instance_actor else None,
                endpoints=endpoints,
                features=features,
                last_updated=datetime.utcnow()
            )

            # Cache result
            await self.cache.set(cache_key, info)
            return info

        except Exception as e:
            logger.error(f"Instance discovery failed for {domain}: {e}")
            raise DiscoveryError(f"Instance discovery failed: {e}")

    async def discover_nodeinfo(self, domain: str) -> Optional[NodeInfo]:
        """
        Discover NodeInfo data.
        
        Implements NodeInfo 2.0 and 2.1 discovery.
        """
        try:
            # Try well-known location first
            well_known_url = f"https://{domain}/.well-known/nodeinfo"
            async with self.session.get(well_known_url) as response:
                if response.status != 200:
                    return None
                    
                links = await response.json()
                nodeinfo_url = None
                
                # Find highest supported version
                for link in links.get('links', []):
                    if link.get('rel') == 'http://nodeinfo.diaspora.software/ns/schema/2.1':
                        nodeinfo_url = link.get('href')
                        break
                    elif link.get('rel') == 'http://nodeinfo.diaspora.software/ns/schema/2.0':
                        nodeinfo_url = link.get('href')
                        
                if not nodeinfo_url:
                    return None
                    
                # Fetch NodeInfo
                async with self.session.get(nodeinfo_url) as nodeinfo_response:
                    if nodeinfo_response.status != 200:
                        return None
                        
                    data = await nodeinfo_response.json()
                    return NodeInfo(
                        version=data.get('version', '2.0'),
                        software=data.get('software', {}),
                        protocols=data.get('protocols', []),
                        services=data.get('services', {}),
                        usage=data.get('usage', {}),
                        open_registrations=data.get('openRegistrations', False),
                        metadata=data.get('metadata', {})
                    )

        except Exception as e:
            logger.error(f"NodeInfo discovery failed for {domain}: {e}")
            return None

    async def discover_instance_actor(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Discover instance actor.
        
        Tries multiple common locations.
        """
        try:
            locations = [
                f"https://{domain}/actor",
                f"https://{domain}/instance",
                f"https://{domain}/instance/actor",
                f"https://{domain}/"
            ]
            
            headers = {
                "Accept": "application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\""
            }
            
            for url in locations:
                try:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('type') in ['Application', 'Service']:
                                return data
                except:
                    continue
                    
            return None

        except Exception as e:
            logger.error(f"Instance actor discovery failed for {domain}: {e}")
            return None

    async def discover_endpoints(self, domain: str) -> Dict[str, str]:
        """
        Discover instance endpoints.
        
        Finds common ActivityPub endpoints.
        """
        endpoints = {}
        base_url = f"https://{domain}"
        
        # Common endpoint paths
        paths = {
            'inbox': '/inbox',
            'outbox': '/outbox',
            'following': '/following',
            'followers': '/followers',
            'featured': '/featured',
            'shared_inbox': '/inbox',
            'nodeinfo': '/.well-known/nodeinfo',
            'webfinger': '/.well-known/webfinger'
        }
        
        for name, path in paths.items():
            url = urljoin(base_url, path)
            try:
                async with self.session.head(url) as response:
                    if response.status != 404:
                        endpoints[name] = url
            except:
                continue
                
        return endpoints

    async def discover_features(self, domain: str) -> Dict[str, bool]:
        """
        Discover supported features.
        
        Checks for various federation features.
        """
        features = {
            'activitypub': False,
            'webfinger': False,
            'nodeinfo': False,
            'shared_inbox': False,
            'collections': False,
            'media_proxy': False
        }
        
        # Check WebFinger
        try:
            webfinger_url = f"https://{domain}/.well-known/webfinger?resource=acct:test@{domain}"
            async with self.session.head(webfinger_url) as response:
                features['webfinger'] = response.status != 404
        except:
            pass
            
        # Check NodeInfo
        try:
            nodeinfo_url = f"https://{domain}/.well-known/nodeinfo"
            async with self.session.head(nodeinfo_url) as response:
                features['nodeinfo'] = response.status == 200
        except:
            pass
            
        # Check shared inbox
        try:
            inbox_url = f"https://{domain}/inbox"
            async with self.session.head(inbox_url) as response:
                features['shared_inbox'] = response.status != 404
        except:
            pass
            
        # Check collections
        try:
            collections = ['/following', '/followers', '/featured']
            features['collections'] = any(
                await self._check_endpoint(domain, path)
                for path in collections
            )
        except:
            pass
            
        # Check media proxy
        try:
            proxy_url = f"https://{domain}/proxy"
            async with self.session.head(proxy_url) as response:
                features['media_proxy'] = response.status != 404
        except:
            pass
            
        # ActivityPub is supported if basic endpoints exist
        features['activitypub'] = features['shared_inbox'] or features['collections']
        
        return features

    async def _check_endpoint(self, domain: str, path: str) -> bool:
        """Check if endpoint exists."""
        try:
            url = f"https://{domain}{path}"
            async with self.session.head(url) as response:
                return response.status != 404
        except:
            return False

    async def webfinger(self,
                       resource: str,
                       domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Perform WebFinger lookup.
        
        Args:
            resource: Resource to look up (acct: or https:)
            domain: Optional domain override
            
        Returns:
            WebFinger response data
        """
        try:
            if not domain:
                if resource.startswith('acct:'):
                    domain = resource.split('@')[1]
                else:
                    domain = urlparse(resource).netloc
                    
            url = (
                f"https://{domain}/.well-known/webfinger"
                f"?resource={resource}"
            )
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                    
                return await response.json()

        except Exception as e:
            logger.error(f"WebFinger lookup failed for {resource}: {e}")
            return None
    async def close(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
