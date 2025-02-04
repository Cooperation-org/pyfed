"""
Integration middleware implementation.
"""

from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
from datetime import datetime
import json

from ..utils.exceptions import MiddlewareError
from ..utils.logging import get_logger
from ..security.http_signatures import HTTPSignatureVerifier
from ..federation.rate_limit import RateLimiter

logger = get_logger(__name__)

class ActivityPubMiddleware:
    """ActivityPub middleware."""

    def __init__(self,
                 signature_verifier: HTTPSignatureVerifier,
                 rate_limiter: RateLimiter):
        self.signature_verifier = signature_verifier
        self.rate_limiter = rate_limiter

    async def process_request(self,
                            method: str,
                            path: str,
                            headers: Dict[str, str],
                            body: Optional[Dict[str, Any]] = None) -> bool:
        """
        Process incoming request.
        
        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            
        Returns:
            bool: True if request is valid
        """
        try:
            # Verify HTTP signature
            if not await self.signature_verifier.verify_request(
                headers=headers,
                method=method,
                path=path
            ):
                return False
            
            # Check rate limits
            domain = headers.get('Host', '').split(':')[0]
            if not await self.rate_limiter.check_limit(domain, 'request'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            return False

    async def process_response(self,
                             status: int,
                             headers: Dict[str, str],
                             body: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Process outgoing response.
        
        Args:
            status: Response status
            headers: Response headers
            body: Response body
            
        Returns:
            Dict with processed headers
        """
        try:
            response_headers = headers.copy()
            
            # Add standard headers
            response_headers.update({
                "Content-Type": "application/activity+json",
                "Vary": "Accept, Accept-Encoding",
                "Cache-Control": "max-age=0, private, must-revalidate"
            })
            
            return response_headers
            
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            return headers 