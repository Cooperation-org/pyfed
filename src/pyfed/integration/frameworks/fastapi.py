"""
FastAPI integration implementation.
"""

from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import json

from ..base import BaseIntegration, IntegrationConfig
from ...utils.exceptions import IntegrationError
from ...utils.logging import get_logger
from ...storage import StorageBackend
from ...federation.delivery import ActivityDelivery
from ...security.key_management import KeyManager
from ..middleware import ActivityPubMiddleware

logger = get_logger(__name__)

class FastAPIIntegration(BaseIntegration):
    """FastAPI integration."""

    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.app = FastAPI(title="PyFed ActivityPub")
        self.middleware = None
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.post("/inbox")
        async def shared_inbox(request: Request):
            """Handle shared inbox."""
            try:
                # Verify request
                if not await self.middleware.process_request(
                    method=request.method,
                    path=request.url.path,
                    headers=dict(request.headers),
                    body=await request.json()
                ):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Handle activity
                activity = await request.json()
                result = await self.handle_activity(activity)
                
                return Response(
                    content=json.dumps({"id": result}),
                    media_type="application/activity+json",
                    status_code=202
                )
                
            except Exception as e:
                logger.error(f"Inbox error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/actor")
        async def get_instance_actor():
            """Get instance actor."""
            try:
                return Response(
                    content=json.dumps(self.instance.actor),
                    media_type="application/activity+json"
                )
            except Exception as e:
                logger.error(f"Actor error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/.well-known/nodeinfo")
        async def get_nodeinfo():
            """Get NodeInfo."""
            try:
                return Response(
                    content=json.dumps(await self.instance.get_nodeinfo()),
                    media_type="application/json"
                )
            except Exception as e:
                logger.error(f"NodeInfo error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

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
            
            logger.info("FastAPI integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize FastAPI integration: {e}")
            raise IntegrationError(f"Integration initialization failed: {e}")

    async def shutdown(self) -> None:
        """Shutdown integration."""
        try:
            await self.storage.close()
            await self.delivery.close()
            await self.key_manager.close()
            
        except Exception as e:
            logger.error(f"Failed to shutdown FastAPI integration: {e}")
            raise IntegrationError(f"Integration shutdown failed: {e}")

    async def handle_activity(self, activity: Dict[str, Any]) -> Optional[str]:
        """Handle incoming activity."""
        return await self.delivery.process_activity(activity)

    async def deliver_activity(self,
                             activity: Dict[str, Any],
                             recipients: List[str]) -> None:
        """Deliver activity to recipients."""
        await self.delivery.deliver_activity(activity, recipients) 