"""
Configuration management implementation.
"""

from typing import Dict, Any, Optional
import yaml
import json
from pathlib import Path
import os
from dataclasses import dataclass, asdict

from ..utils.exceptions import ConfigError
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    min_connections: int = 5
    max_connections: int = 20
    timeout: int = 30

@dataclass
class RedisConfig:
    """Redis configuration."""
    url: str
    pool_size: int = 10
    timeout: int = 30

@dataclass
class SecurityConfig:
    """Security configuration."""
    key_path: str
    signature_ttl: int = 300
    max_payload_size: int = 5_000_000
    allowed_algorithms: list = None

    def __post_init__(self):
        if self.allowed_algorithms is None:
            self.allowed_algorithms = ["rsa-sha256"]

@dataclass
class FederationConfig:
    """Federation configuration."""
    domain: str
    shared_inbox: bool = True
    delivery_timeout: int = 30
    max_recipients: int = 100
    retry_delay: int = 300

@dataclass
class MediaConfig:
    """Media configuration."""
    upload_path: str
    max_size: int = 10_000_000
    allowed_types: list = None

    def __post_init__(self):
        if self.allowed_types is None:
            self.allowed_types = [
                'image/jpeg',
                'image/png',
                'image/gif',
                'video/mp4',
                'audio/mpeg'
            ]

@dataclass
class ApplicationConfig:
    """Application configuration."""
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    federation: FederationConfig
    media: MediaConfig
    debug: bool = False

class ConfigurationManager:
    """Manage application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = None

    def load_config(self) -> ApplicationConfig:
        """Load configuration."""
        try:
            # Load from file if specified
            if self.config_path:
                return self._load_from_file(self.config_path)
            
            # Load from environment
            return self._load_from_env()
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise ConfigError(f"Failed to load config: {e}")

    def _load_from_file(self, path: str) -> ApplicationConfig:
        """Load configuration from file."""
        try:
            with open(path) as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                    
            return self._create_config(data)
            
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {e}")

    def _load_from_env(self) -> ApplicationConfig:
        """Load configuration from environment variables."""
        try:
            return ApplicationConfig(
                database=DatabaseConfig(
                    url=os.getenv('DATABASE_URL', 'sqlite:///pyfed.db'),
                    min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '5')),
                    max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),
                    timeout=int(os.getenv('DB_TIMEOUT', '30'))
                ),
                redis=RedisConfig(
                    url=os.getenv('REDIS_URL', 'redis://localhost'),
                    pool_size=int(os.getenv('REDIS_POOL_SIZE', '10')),
                    timeout=int(os.getenv('REDIS_TIMEOUT', '30'))
                ),
                security=SecurityConfig(
                    key_path=os.getenv('KEY_PATH', 'keys'),
                    signature_ttl=int(os.getenv('SIGNATURE_TTL', '300')),
                    max_payload_size=int(os.getenv('MAX_PAYLOAD_SIZE', '5000000'))
                ),
                federation=FederationConfig(
                    domain=os.getenv('DOMAIN', 'localhost'),
                    shared_inbox=os.getenv('SHARED_INBOX', 'true').lower() == 'true',
                    delivery_timeout=int(os.getenv('DELIVERY_TIMEOUT', '30')),
                    max_recipients=int(os.getenv('MAX_RECIPIENTS', '100'))
                ),
                media=MediaConfig(
                    upload_path=os.getenv('UPLOAD_PATH', 'uploads'),
                    max_size=int(os.getenv('MAX_UPLOAD_SIZE', '10000000'))
                ),
                debug=os.getenv('DEBUG', 'false').lower() == 'true'
            )
            
        except Exception as e:
            raise ConfigError(f"Failed to load config from env: {e}")

    def _create_config(self, data: Dict[str, Any]) -> ApplicationConfig:
        """Create config from dictionary."""
        try:
            return ApplicationConfig(
                database=DatabaseConfig(**data.get('database', {})),
                redis=RedisConfig(**data.get('redis', {})),
                security=SecurityConfig(**data.get('security', {})),
                federation=FederationConfig(**data.get('federation', {})),
                media=MediaConfig(**data.get('media', {})),
                debug=data.get('debug', False)
            )
        except Exception as e:
            raise ConfigError(f"Invalid config data: {e}")

    def save_config(self, config: ApplicationConfig, path: str) -> None:
        """Save configuration to file."""
        try:
            data = asdict(config)
            
            with open(path, 'w') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2)
                    
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}") 