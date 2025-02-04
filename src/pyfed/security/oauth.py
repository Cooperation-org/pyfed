"""
Enhanced OAuth2 implementation for ActivityPub C2S authentication.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiohttp
import jwt
from datetime import datetime, timedelta
import asyncio
from abc import ABC, abstractmethod
from ..utils.exceptions import AuthenticationError
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class OAuth2Config:
    """OAuth2 configuration."""
    token_lifetime: int = 3600  # 1 hour
    refresh_token_lifetime: int = 2592000  # 30 days
    clock_skew: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: float = 10.0
    allowed_grant_types: List[str] = ("password", "refresh_token")
    allowed_scopes: List[str] = ("read", "write")
    required_token_fields: List[str] = (
        "access_token",
        "token_type",
        "expires_in",
        "refresh_token"
    )

class TokenCache(ABC):
    """Abstract token cache interface."""
    
    @abstractmethod
    async def get_token(self, key: str) -> Optional[Dict[str, Any]]:
        """Get token from cache."""
        pass
        
    @abstractmethod
    async def store_token(self, key: str, token_data: Dict[str, Any]) -> None:
        """Store token in cache."""
        pass
        
    @abstractmethod
    async def invalidate_token(self, key: str) -> None:
        """Invalidate cached token."""
        pass

class OAuth2Handler:
    """Enhanced OAuth2 handler with improved security."""
    
    def __init__(self, 
                 client_id: str,
                 client_secret: str,
                 token_endpoint: str,
                 config: Optional[OAuth2Config] = None,
                 token_cache: Optional[TokenCache] = None):
        """Initialize OAuth2 handler."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.config = config or OAuth2Config()
        self.token_cache = token_cache
        self._lock = asyncio.Lock()
        
        # Metrics
        self.metrics = {
            'tokens_created': 0,
            'tokens_refreshed': 0,
            'tokens_verified': 0,
            'token_failures': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    async def create_token(self, 
                          username: str, 
                          password: str,
                          scope: Optional[str] = None) -> Dict[str, Any]:
        """
        Create OAuth2 token using password grant.
        
        Args:
            username: User's username
            password: User's password
            scope: Optional scope request
            
        Returns:
            Token response data
            
        Raises:
            AuthenticationError: If token creation fails
        """
        async with self._lock:
            try:
                # Validate scope
                if scope and not self._validate_scope(scope):
                    raise AuthenticationError(f"Invalid scope: {scope}")
                
                data = {
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': scope or ' '.join(self.config.allowed_scopes)
                }
                
                token_data = await self._make_token_request(data)
                
                # Cache token if cache available
                if self.token_cache:
                    await self.token_cache.store_token(username, token_data)
                
                self.metrics['tokens_created'] += 1
                return token_data
                
            except AuthenticationError:
                self.metrics['token_failures'] += 1
                raise
            except Exception as e:
                self.metrics['token_failures'] += 1
                logger.error(f"Token creation failed: {e}")
                raise AuthenticationError(f"Token creation failed: {e}")

    async def refresh_token(self, 
                          refresh_token: str,
                          user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh OAuth2 token.
        
        Args:
            refresh_token: Refresh token
            user_id: Optional user ID for cache
            
        Returns:
            New token data
            
        Raises:
            AuthenticationError: If refresh fails
        """
        async with self._lock:
            try:
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
                
                token_data = await self._make_token_request(data)
                
                # Update cache
                if user_id and self.token_cache:
                    await self.token_cache.store_token(user_id, token_data)
                
                self.metrics['tokens_refreshed'] += 1
                return token_data
                
            except Exception as e:
                self.metrics['token_failures'] += 1
                logger.error(f"Token refresh failed: {e}")
                raise AuthenticationError(f"Token refresh failed: {e}")

    async def verify_token(self, 
                          token: str,
                          required_scope: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify OAuth2 token.
        
        Args:
            token: Token to verify
            required_scope: Optional required scope
            
        Returns:
            Token payload if valid
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # First check cache if available
            if self.token_cache:
                cached = await self.token_cache.get_token(token)
                if cached:
                    self.metrics['cache_hits'] += 1
                    return cached
                self.metrics['cache_misses'] += 1
            
            # Verify JWT
            payload = jwt.decode(
                token,
                self.client_secret,
                algorithms=['HS256'],
                leeway=self.config.clock_skew
            )
            
            # Check expiry
            exp = datetime.fromtimestamp(payload['exp'])
            if exp < datetime.utcnow():
                raise AuthenticationError("Token has expired")
                
            # Verify scope if required
            if required_scope:
                token_scopes = payload.get('scope', '').split()
                if required_scope not in token_scopes:
                    raise AuthenticationError(f"Missing required scope: {required_scope}")
            
            self.metrics['tokens_verified'] += 1
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise AuthenticationError(f"Token verification failed: {e}")

    async def _make_token_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make OAuth2 token request with retries.
        
        Args:
            data: Request data
            
        Returns:
            Token response data
            
        Raises:
            AuthenticationError: If request fails
        """
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        
        for attempt in range(self.config.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        self.token_endpoint,
                        data=data,
                        headers={'Accept': 'application/json'}
                    ) as response:
                        if response.status != 200:
                            error_data = await response.text()
                            raise AuthenticationError(
                                f"Token request failed: {response.status} - {error_data}"
                            )
                            
                        token_data = await response.json()
                        
                        # Validate response
                        self._validate_token_response(token_data)
                        
                        return token_data
                        
            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise AuthenticationError(f"Network error: {e}")
                await asyncio.sleep(self.config.retry_delay)
            except AuthenticationError:
                raise
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise AuthenticationError(f"Token request failed: {e}")
                await asyncio.sleep(self.config.retry_delay)

    def _validate_token_response(self, data: Dict[str, Any]) -> None:
        """Validate token response data."""
        if not isinstance(data, dict):
            raise AuthenticationError("Invalid token response format")
            
        missing = set(self.config.required_token_fields) - set(data.keys())
        if missing:
            raise AuthenticationError(f"Missing required fields: {missing}")
            
        if data.get('token_type', '').lower() != 'bearer':
            raise AuthenticationError("Unsupported token type")

    def _validate_scope(self, scope: str) -> bool:
        """Validate requested scope."""
        requested = set(scope.split())
        allowed = set(self.config.allowed_scopes)
        return requested.issubset(allowed)

    async def revoke_token(self, token: str, user_id: Optional[str] = None) -> None:
        """
        Revoke OAuth2 token.
        
        Args:
            token: Token to revoke
            user_id: Optional user ID for cache
        """
        if self.token_cache and user_id:
            await self.token_cache.invalidate_token(user_id)