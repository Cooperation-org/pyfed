"""
Flask integration implementation.
"""

from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, Response
import json

from ..base import BaseIntegration, IntegrationConfig
from ...utils.exceptions import IntegrationError
from ...utils.logging import get_logger
from ...storage import StorageBackend
from ...federation.delivery import ActivityDelivery
from ...security.key_management import KeyManager
from ..middleware import ActivityPubMiddleware

logger = get_logger(__name__)

class FlaskIntegration(BaseIntegration):
    """Flask integration."""

    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.app = Flask(__name__)
        self.middleware = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        @self.app.post("/inbox")
        async def shared_inbox():
            """Handle shared inbox."""
            try:
                # Verify request
                if not await self.middleware.process_request(
                    method=request.method,
                    path=request.path,
                    headers=dict(request.headers),
                    body=request.get_json()
                ):
                    return jsonify({"error": "Unauthorized"}), 401
                
                # Handle activity
                activity = request.get_json()
                result = await self.handle_activity(activity)
                
                return Response(
                    response=json.dumps({"id": result}),
                    status=202,
                    mimetype="application/activity+json"
                )
                
            except Exception as e:
                logger.error(f"Inbox error: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.get("/actor")
        async def get_instance_actor():
            """Get instance actor."""
            try:
                return Response(
                    response=json.dumps(self.instance.actor),
                    mimetype="application/activity+json"
                )
            except Exception as e:
                logger.error(f"Actor error: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.get("/.well-known/nodeinfo")
        async def get_nodeinfo():
            """Get NodeInfo."""
            try:
                return jsonify(await self.instance.get_nodeinfo())
            except Exception as e:
                logger.error(f"NodeInfo error: {e}")
                return jsonify({"error": str(e)}), 500

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
            
            logger.info("Flask integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Flask integration: {e}")
            raise IntegrationError(f"Integration initialization failed: {e}")

    async def shutdown(self) -> None:
        """Shutdown integration."""
        try:
            await self.storage.close()
            await self.delivery.close()
            await self.key_manager.close()
            
        except Exception as e:
            logger.error(f"Failed to shutdown Flask integration: {e}")
            raise IntegrationError(f"Integration shutdown failed: {e}")

    async def handle_activity(self, activity: Dict[str, Any]) -> Optional[str]:
        """Handle incoming activity."""
        return await self.delivery.process_activity(activity)

    async def deliver_activity(self,
                             activity: Dict[str, Any],
                             recipients: List[str]) -> None:
        """Deliver activity to recipients."""
        await self.delivery.deliver_activity(activity, recipients) 