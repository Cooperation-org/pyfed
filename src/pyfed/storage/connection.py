"""
Enhanced connection pooling implementation.
"""

from typing import Dict, Any, Optional, List
import asyncio
import asyncpg
from datetime import datetime
import time
from dataclasses import dataclass
from enum import Enum

from ..utils.exceptions import StorageError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class PoolStrategy(Enum):
    """Connection pool strategies."""
    FIXED = "fixed"
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"

@dataclass
class PoolConfig:
    """Pool configuration."""
    min_size: int
    max_size: int
    strategy: PoolStrategy
    idle_timeout: int  # seconds
    max_queries: int   # per connection
    connection_timeout: int  # seconds

class ConnectionMetrics:
    """Connection pool metrics."""
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.waiting_queries = 0
        self.total_queries = 0
        self.failed_queries = 0
        self.connection_timeouts = 0
        self.query_timeouts = 0

class EnhancedPool:
    """Enhanced connection pool."""

    def __init__(self,
                 dsn: str,
                 config: Optional[PoolConfig] = None):
        self.dsn = dsn
        self.config = config or PoolConfig(
            min_size=5,
            max_size=20,
            strategy=PoolStrategy.ADAPTIVE,
            idle_timeout=300,
            max_queries=1000,
            connection_timeout=30
        )
        self.pool: Optional[asyncpg.Pool] = None
        self.metrics = ConnectionMetrics()
        self._monitor_task = None
        self._cleanup_task = None
        self._connection_stats: Dict[asyncpg.Connection, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize connection pool."""
        try:
            # Create pool
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.connection_timeout
            )
            
            # Start monitoring
            self._monitor_task = asyncio.create_task(self._monitor_pool())
            self._cleanup_task = asyncio.create_task(self._cleanup_connections())
            
            logger.info(
                f"Connection pool initialized with strategy: {self.config.strategy.value}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise StorageError(f"Pool initialization failed: {e}")

    async def acquire(self) -> asyncpg.Connection:
        """
        Acquire database connection.
        
        Implements connection management based on strategy.
        """
        try:
            # Update metrics
            self.metrics.waiting_queries += 1
            
            # Get connection
            if self.config.strategy == PoolStrategy.ADAPTIVE:
                conn = await self._get_adaptive_connection()
            else:
                conn = await self.pool.acquire()
            
            # Update stats
            self._connection_stats[conn] = {
                'acquired_at': datetime.utcnow(),
                'queries': 0
            }
            
            self.metrics.active_connections += 1
            self.metrics.waiting_queries -= 1
            
            return conn
            
        except Exception as e:
            self.metrics.waiting_queries -= 1
            self.metrics.connection_timeouts += 1
            logger.error(f"Failed to acquire connection: {e}")
            raise StorageError(f"Failed to acquire connection: {e}")

    async def release(self, conn: asyncpg.Connection) -> None:
        """Release database connection."""
        try:
            # Update stats
            if conn in self._connection_stats:
                del self._connection_stats[conn]
            
            self.metrics.active_connections -= 1
            self.metrics.idle_connections += 1
            
            await self.pool.release(conn)
            
        except Exception as e:
            logger.error(f"Failed to release connection: {e}")
            raise StorageError(f"Failed to release connection: {e}")

    async def _get_adaptive_connection(self) -> asyncpg.Connection:
        """Get connection using adaptive strategy."""
        current_size = self.metrics.total_connections
        active = self.metrics.active_connections
        waiting = self.metrics.waiting_queries
        
        # Check if we need to grow pool
        if (
            current_size < self.config.max_size and
            (active / current_size > 0.75 or waiting > 0)
        ):
            # Grow pool
            await self.pool.set_min_size(min(
                current_size + 5,
                self.config.max_size
            ))
            
        return await self.pool.acquire()

    async def _monitor_pool(self) -> None:
        """Monitor pool health and performance."""
        while True:
            try:
                # Update metrics
                self.metrics.total_connections = len(self._connection_stats)
                
                # Log metrics
                logger.debug(
                    f"Pool metrics - Total: {self.metrics.total_connections}, "
                    f"Active: {self.metrics.active_connections}, "
                    f"Idle: {self.metrics.idle_connections}, "
                    f"Waiting: {self.metrics.waiting_queries}"
                )
                
                # Adjust pool size if needed
                if self.config.strategy == PoolStrategy.ADAPTIVE:
                    await self._adjust_pool_size()
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Pool monitoring failed: {e}")
                await asyncio.sleep(300)

    async def _adjust_pool_size(self) -> None:
        """Adjust pool size based on usage."""
        current_size = self.metrics.total_connections
        active = self.metrics.active_connections
        
        # Shrink if underutilized
        if active / current_size < 0.25 and current_size > self.config.min_size:
            new_size = max(
                current_size - 5,
                self.config.min_size
            )
            await self.pool.set_min_size(new_size)
            
        # Grow if heavily utilized
        elif active / current_size > 0.75 and current_size < self.config.max_size:
            new_size = min(
                current_size + 5,
                self.config.max_size
            )
            await self.pool.set_min_size(new_size)

    async def _cleanup_connections(self) -> None:
        """Clean up idle and overused connections."""
        while True:
            try:
                now = datetime.utcnow()
                
                # Check each connection
                for conn, stats in self._connection_stats.items():
                    # Check idle timeout
                    idle_time = (now - stats['acquired_at']).total_seconds()
                    if idle_time > self.config.idle_timeout:
                        await self.release(conn)
                        
                    # Check query limit
                    if stats['queries'] >= self.config.max_queries:
                        await self.release(conn)
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Connection cleanup failed: {e}")
                await asyncio.sleep(300)

    async def close(self) -> None:
        """Close connection pool."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self.pool:
            await self.pool.close() 