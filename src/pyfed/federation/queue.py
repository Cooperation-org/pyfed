"""
federation/queue.py
Activity delivery queue implementation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import dataclass
from enum import Enum
import aioredis

from ..utils.exceptions import QueueError
from ..utils.logging import get_logger
from .delivery import ActivityDelivery, DeliveryResult

logger = get_logger(__name__)

class DeliveryStatus(Enum):
    """Delivery status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class QueuedDelivery:
    """Queued delivery item."""
    id: str
    activity: Dict[str, Any]
    recipients: List[str]
    status: DeliveryStatus
    attempts: int
    next_attempt: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None

class DeliveryQueue:
    """Activity delivery queue."""

    def __init__(self,
                 delivery_service: ActivityDelivery,
                 redis_url: str = "redis://localhost",
                 max_attempts: int = 5,
                 batch_size: int = 20):
        self.delivery_service = delivery_service
        self.redis_url = redis_url
        self.max_attempts = max_attempts
        self.batch_size = batch_size
        self.redis: Optional[aioredis.Redis] = None
        self._processing_task = None

    async def initialize(self) -> None:
        """Initialize queue."""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            self._processing_task = asyncio.create_task(self._process_queue_loop())
        except Exception as e:
            logger.error(f"Failed to initialize queue: {e}")
            raise QueueError(f"Queue initialization failed: {e}")

    async def enqueue(self,
                     activity: Dict[str, Any],
                     recipients: List[str],
                     priority: int = 0) -> str:
        """
        Queue activity for delivery.
        
        Args:
            activity: Activity to deliver
            recipients: List of recipient inboxes
            priority: Delivery priority (0-9, higher is more urgent)
            
        Returns:
            Delivery ID
        """
        try:
            # Create delivery record
            delivery_id = f"delivery_{datetime.utcnow().timestamp()}"
            delivery = QueuedDelivery(
                id=delivery_id,
                activity=activity,
                recipients=recipients,
                status=DeliveryStatus.PENDING,
                attempts=0,
                next_attempt=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store in Redis
            await self.redis.set(
                f"delivery:{delivery_id}",
                json.dumps(delivery.__dict__)
            )
            
            # Add to priority queue
            score = datetime.utcnow().timestamp() + (9 - priority) * 10
            await self.redis.zadd(
                "delivery_queue",
                {delivery_id: score}
            )
            
            logger.info(f"Queued delivery {delivery_id} with priority {priority}")
            return delivery_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue delivery: {e}")
            raise QueueError(f"Failed to enqueue delivery: {e}")

    async def get_status(self, delivery_id: str) -> Optional[QueuedDelivery]:
        """Get delivery status."""
        try:
            data = await self.redis.get(f"delivery:{delivery_id}")
            if data:
                return QueuedDelivery(**json.loads(data))
            return None
        except Exception as e:
            logger.error(f"Failed to get delivery status: {e}")
            raise QueueError(f"Failed to get delivery status: {e}")

    async def _process_queue_loop(self) -> None:
        """Background task for processing queue."""
        while True:
            try:
                # Get batch of deliveries
                now = datetime.utcnow().timestamp()
                delivery_ids = await self.redis.zrangebyscore(
                    "delivery_queue",
                    "-inf",
                    now,
                    start=0,
                    num=self.batch_size
                )
                
                if not delivery_ids:
                    await asyncio.sleep(1)
                    continue
                
                # Process deliveries
                for delivery_id in delivery_ids:
                    await self._process_delivery(delivery_id)
                    
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)

    async def _process_delivery(self, delivery_id: str) -> None:
        """Process a single delivery."""
        try:
            # Get delivery data
            data = await self.redis.get(f"delivery:{delivery_id}")
            if not data:
                return
                
            delivery = QueuedDelivery(**json.loads(data))
            
            # Update status
            delivery.status = DeliveryStatus.IN_PROGRESS
            delivery.attempts += 1
            delivery.updated_at = datetime.utcnow()
            
            # Attempt delivery
            try:
                result = await self.delivery_service.deliver_activity(
                    activity=delivery.activity,
                    recipients=delivery.recipients
                )
                
                if result.success:
                    delivery.status = DeliveryStatus.COMPLETED
                else:
                    delivery.status = DeliveryStatus.FAILED
                    delivery.error = result.error_message
                    
                    # Schedule retry if attempts remain
                    if delivery.attempts < self.max_attempts:
                        delivery.status = DeliveryStatus.RETRYING
                        delivery.next_attempt = datetime.utcnow() + timedelta(
                            minutes=2 ** delivery.attempts
                        )
                        
                        # Re-queue with backoff
                        await self.redis.zadd(
                            "delivery_queue",
                            {delivery_id: delivery.next_attempt.timestamp()}
                        )
                    
            except Exception as e:
                delivery.status = DeliveryStatus.FAILED
                delivery.error = str(e)
            
            # Update delivery record
            await self.redis.set(
                f"delivery:{delivery_id}",
                json.dumps(delivery.__dict__)
            )
            
            # Remove from queue if complete
            if delivery.status in [DeliveryStatus.COMPLETED, DeliveryStatus.FAILED]:
                await self.redis.zrem("delivery_queue", delivery_id)
                
        except Exception as e:
            logger.error(f"Failed to process delivery {delivery_id}: {e}")

    async def close(self) -> None:
        """Clean up resources."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
        if self.redis:
            await self.redis.close() 