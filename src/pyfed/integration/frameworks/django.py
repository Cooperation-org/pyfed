"""
Django integration implementation.
"""

from typing import Dict, Any, Optional, List
from django.http import HttpRequest, JsonResponse, HttpResponseBadRequest
from django.views import View
from django.conf import settings
import json
import asyncio

from ..base import BaseIntegration, IntegrationConfig
from ...utils.exceptions import IntegrationError
from ...utils.logging import get_logger
from ...storage import StorageBackend
from ...federation.delivery import ActivityDelivery
from ...security.key_management import KeyManager
from ..middleware import ActivityPubMiddleware

logger = get_logger(__name__)

class DjangoIntegration(BaseIntegration):
    """Django integration."""

    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.middleware = None
        self._setup_views()

    def _setup_views(self) -> None:
        """Setup Django views."""
        
        class InboxView(View):
            """Shared inbox view."""
            
            async def post(self, request: HttpRequest):
                try:
                    # Verify request
                    if not await self.middleware.process_request(
                        method=request.method,
                        path=request.path,
                        headers=dict(request.headers),
                        body=json.loads(request.body)
                    ):
                        return JsonResponse(
                            {"error": "Unauthorized"},
                            status=401
                        )
                    
                    # Handle activity
                    activity = json.loads(request.body)
                    result = await self.handle_activity(activity)
                    
                    return JsonResponse(
                        {"id": result},
                        status=202,
                        content_type="application/activity+json"
                    )
                    
                except Exception as e:
                    logger.error(f"Inbox error: {e}")
                    return JsonResponse(
                        {"error": str(e)},
                        status=500
                    )

        class ActorView(View):
            """Instance actor view."""
            
            async def get(self, request: HttpRequest):
                try:
                    return JsonResponse(
                        self.instance.actor,
                        content_type="application/activity+json"
                    )
                except Exception as e:
                    logger.error(f"Actor error: {e}")
                    return JsonResponse(
                        {"error": str(e)},
                        status=500
                    )

        class NodeInfoView(View):
            """NodeInfo view."""
            
            async def get(self, request: HttpRequest):
                try:
                    nodeinfo = await self.instance.get_nodeinfo()
                    return JsonResponse(nodeinfo)
                except Exception as e:
                    logger.error(f"NodeInfo error: {e}")
                    return JsonResponse(
                        {"error": str(e)},
                        status=500
                    )

        # Store view classes
        self.views = {
            'inbox': InboxView,
            'actor': ActorView,
            'nodeinfo': NodeInfoView
        }

    async def initialize(self) -> None:
        """Initialize integration."""
        try:
            # Initialize components
            self.storage = StorageBackend.create(
                provider="postgresql",
                database_url=self.config.database_url
            )
            await self.storage.initialize()
            
            self.key_manager = KeyManager(self.config.key_path)
            await self.key_manager.initialize()
            
            self.delivery = ActivityDelivery(
                storage=self.storage,
                key_manager=self.key_manager
            )
            await self.delivery.initialize()
            
            # Initialize middleware
            self.middleware = ActivityPubMiddleware(
                signature_verifier=self.key_manager.signature_verifier,
                rate_limiter=self.delivery.rate_limiter
            )
            
            logger.info("Django integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Django integration: {e}")
            raise IntegrationError(f"Integration initialization failed: {e}")

    async def shutdown(self) -> None:
        """Shutdown integration."""
        try:
            await self.storage.close()
            await self.delivery.close()
            await self.key_manager.close()
            
        except Exception as e:
            logger.error(f"Failed to shutdown Django integration: {e}")
            raise IntegrationError(f"Integration shutdown failed: {e}")

    async def handle_activity(self, activity: Dict[str, Any]) -> Optional[str]:
        """Handle incoming activity."""
        return await self.delivery.process_activity(activity)

    async def deliver_activity(self,
                             activity: Dict[str, Any],
                             recipients: List[str]) -> None:
        """Deliver activity to recipients."""
        await self.delivery.deliver_activity(activity, recipients) 