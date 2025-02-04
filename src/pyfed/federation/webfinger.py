"""
WebFinger protocol implementation.
"""

from typing import Dict, Any, Optional
import aiohttp
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

class WebFingerClient:
    """WebFinger client implementation."""

    def __init__(self, verify_ssl: bool = True):
        self.verify_ssl = verify_ssl
        self.session = None

    async def initialize(self) -> None:
        """Initialize client."""
        ssl = None if self.verify_ssl else False
        self.session = aiohttp.ClientSession(
            headers={"Accept": "application/jrd+json, application/json"},
            connector=aiohttp.TCPConnector(ssl=ssl)
        )

    async def finger(self, account: str) -> Optional[Dict[str, Any]]:
        """
        Perform WebFinger lookup.
        
        Args:
            account: Account to look up (e.g., user@domain.com)
            
        Returns:
            WebFinger response if found
        """
        try:
            if not '@' in account:
                return None

            # Ensure acct: prefix
            if not account.startswith('acct:'):
                account = f"acct:{account}"

            domain = account.split('@')[-1]
            url = f"https://{domain}/.well-known/webfinger?resource={quote(account)}"

            response = await self.session.get(url)
            async with response as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

        except Exception as e:
            logger.error(f"WebFinger lookup failed for {account}: {e}")
            return None

    async def get_actor_url(self, account: str) -> Optional[str]:
        """
        Get actor URL from WebFinger response.
        
        Args:
            account: Account to look up
            
        Returns:
            Actor URL if found
        """
        try:
            data = await self.finger(account)
            if not data:
                return None

            for link in data.get('links', []):
                if (link.get('rel') == 'self' and 
                    link.get('type') == 'application/activity+json'):
                    return link.get('href')
            return None

        except Exception as e:
            logger.error(f"Failed to get actor URL for {account}: {e}")
            return None

    async def get_inbox_url(self, account: str) -> Optional[str]:
        """
        Get inbox URL for account.
        
        Args:
            account: Account to look up
            
        Returns:
            Inbox URL if found
        """
        try:
            actor_url = await self.get_actor_url(account)
            logger.debug(f"actor_url: {actor_url}")
            if not actor_url:
                return None

            response = await self.session.get(actor_url)
            async with response as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get('inbox')

        except Exception as e:
            logger.error(f"Failed to get inbox URL for {account}: {e}")
            return None

    async def close(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close() 