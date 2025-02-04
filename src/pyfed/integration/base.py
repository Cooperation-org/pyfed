"""
Base integration interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml
import json
from pathlib import Path

from ..utils.exceptions import IntegrationError
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class IntegrationConfig:
    """Integration configuration."""
    domain: str
    database_url: str
    redis_url: str
    media_path: str
    key_path: str
    max_payload_size: int = 5_000_000  # 5MB
    request_timeout: int = 30
    debug: bool = False

class BaseIntegration(ABC):
    """Base integration interface."""

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.app = None
        self.storage = None
        self.delivery = None
        self.key_manager = None
        self.instance = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize integration."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown integration."""
        pass

    @abstractmethod
    async def handle_activity(self, activity: Dict[str, Any]) -> Optional[str]:
        """Handle incoming activity."""
        pass

    @abstractmethod
    async def deliver_activity(self,
                             activity: Dict[str, Any],
                             recipients: List[str]) -> None:
        """Deliver activity to recipients."""
        pass

    @classmethod
    def load_config(cls, config_path: str) -> IntegrationConfig:
        """Load configuration from file."""
        try:
            with open(config_path) as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                    
            return IntegrationConfig(**data)
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise IntegrationError(f"Failed to load config: {e}") 