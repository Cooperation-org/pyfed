"""
federation/rate_limit.py
Federation rate limiting implementation.

Features:
- Per-domain rate limiting
- Multiple rate limit strategies
- In-memory storage
- Configurable limits
- Burst handling
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum
import json
from ..utils.exceptions import RateLimitError
from ..utils.logging import get_logger
from ..cache.memory_cache import MemoryCache

logger = get_logger(__name__)

class RateLimitStrategy(Enum):
    """Rate limit strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int
    period: int  # seconds
    burst: Optional[int] = None

@dataclass
class RateLimitState:
    """Current rate limit state."""
    remaining: int
    reset: datetime
    limit: int

class RateLimiter:
    """Federation rate limiting."""

    def __init__(
        self,
        default_limit: Optional[RateLimit] = None,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
        ttl: int = 3600  # 1 hour default TTL
    ):
        """Initialize rate limiter.
        
        Args:
            default_limit: Default rate limit configuration
            strategy: Rate limiting strategy
            ttl: Cache TTL in seconds
        """
        self.default_limit = default_limit or RateLimit(
            requests=100,
            period=60,  # 100 requests per minute
            burst=20
        )
        self.strategy = strategy
        self.cache = MemoryCache(ttl)
        
    async def _get_state(self, domain: str) -> RateLimitState:
        """Get current rate limit state for domain."""
        state = await self.cache.get(f"ratelimit:{domain}")
        if not state:
            state = RateLimitState(
                remaining=self.default_limit.requests,
                reset=datetime.now() + timedelta(seconds=self.default_limit.period),
                limit=self.default_limit.requests
            )
            await self._set_state(domain, state)
        return state
        
    async def _set_state(self, domain: str, state: RateLimitState) -> None:
        """Set rate limit state for domain."""
        await self.cache.set(f"ratelimit:{domain}", state)
        
    async def check_rate_limit(self, domain: str) -> bool:
        """Check if domain is rate limited."""
        state = await self._get_state(domain)
        
        # Reset if expired
        if datetime.now() >= state.reset:
            state = RateLimitState(
                remaining=self.default_limit.requests,
                reset=datetime.now() + timedelta(seconds=self.default_limit.period),
                limit=self.default_limit.requests
            )
            await self._set_state(domain, state)
            return True
            
        if state.remaining <= 0:
            return False
            
        # Update remaining
        state.remaining -= 1
        await self._set_state(domain, state)
        return True
        
    async def get_wait_time(self, domain: str) -> float:
        """Get wait time in seconds until rate limit reset."""
        state = await self._get_state(domain)
        if state.remaining > 0:
            return 0
        
        wait_time = (state.reset - datetime.now()).total_seconds()
        return max(0, wait_time)
        
    async def update_rate_limit(
        self,
        domain: str,
        headers: Dict[str, str]
    ) -> None:
        """Update rate limit state from response headers."""
        remaining = headers.get('X-RateLimit-Remaining')
        reset = headers.get('X-RateLimit-Reset')
        limit = headers.get('X-RateLimit-Limit')
        
        if remaining is not None and reset is not None and limit is not None:
            state = RateLimitState(
                remaining=int(remaining),
                reset=datetime.fromtimestamp(int(reset)),
                limit=int(limit)
            )
            await self._set_state(domain, state)
            
    async def clear(self, domain: str) -> None:
        """Clear rate limit state for domain."""
        await self.cache.delete(f"ratelimit:{domain}")
        
    async def clear_all(self) -> None:
        """Clear all rate limit states."""
        await self.cache.clear()