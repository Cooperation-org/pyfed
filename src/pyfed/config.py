"""
PyFed configuration management.
"""

from typing import Dict, Any, Optional, List
from dataclasses import asdict, dataclass, field
from pathlib import Path
import yaml
import json
import os

from .utils.exceptions import ConfigError
from .utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    min_connections: int = 5
    max_connections: int = 20
    timeout: int = 30

@dataclass
class SecurityConfig:
    """Security configuration."""
    domain: str
    key_path: str
    private_key_path: Optional[str] = None
    public_key_path: Optional[str] = None
    signature_ttl: int = 300  # 5 minutes
    max_payload_size: int = 5_000_000  # 5MB
    allowed_algorithms: List[str] = field(default_factory=lambda: ["rsa-sha256"])

@dataclass
class FederationConfig:
    """Federation configuration."""
    domain: str
    shared_inbox: bool = True
    delivery_timeout: int = 30
    max_recipients: int = 100
    retry_delay: int = 300
    verify_ssl: bool = True

@dataclass
class MediaConfig:
    """Media configuration."""
    upload_path: str
    max_size: int = 10_000_000  # 10MB
    allowed_types: List[str] = field(default_factory=lambda: [
        'image/jpeg',
        'image/png',
        'image/gif',
        'video/mp4',
        'audio/mpeg'
    ])

@dataclass
class StorageConfig:
    """Storage configuration."""
    provider: str = "sqlite"
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        url="sqlite:///pyfed.db"
    ))

@dataclass
class PyFedConfig:
    """Main PyFed configuration."""
    domain: str
    storage: StorageConfig
    security: SecurityConfig
    federation: FederationConfig
    media: MediaConfig
    debug: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PyFedConfig':
        """Create config from dictionary."""
        try:
            # Create nested configs
            storage_config = StorageConfig(
                provider=data.get('storage', {}).get('provider', 'sqlite'),
                database=DatabaseConfig(**data.get('storage', {}).get('database', {}))
            )

            security_config = SecurityConfig(
                domain=data['domain'],
                **data.get('security', {})
            )

            federation_config = FederationConfig(
                domain=data['domain'],
                **data.get('federation', {})
            )

            media_config = MediaConfig(
                upload_path=data.get('media', {}).get('upload_path', 'uploads'),
                **data.get('media', {})
            )

            return cls(
                domain=data['domain'],
                storage=storage_config,
                security=security_config,
                federation=federation_config,
                media=media_config,
                debug=data.get('debug', False)
            )

        except Exception as e:
            raise ConfigError(f"Failed to create config: {e}")

    @classmethod
    def from_file(cls, path: str) -> 'PyFedConfig':
        """Load configuration from file."""
        try:
            with open(path) as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {e}")

    @classmethod
    def from_env(cls) -> 'PyFedConfig':
        """Load configuration from environment variables."""
        try:
            return cls(
                domain=os.getenv('PYFED_DOMAIN', 'localhost'),
                storage=StorageConfig(
                    provider=os.getenv('PYFED_STORAGE_PROVIDER', 'sqlite'),
                    database=DatabaseConfig(
                        url=os.getenv('PYFED_DATABASE_URL', 'sqlite:///pyfed.db'),
                        min_connections=int(os.getenv('PYFED_DB_MIN_CONNECTIONS', '5')),
                        max_connections=int(os.getenv('PYFED_DB_MAX_CONNECTIONS', '20')),
                        timeout=int(os.getenv('PYFED_DB_TIMEOUT', '30'))
                    )
                ),
                security=SecurityConfig(
                    domain=os.getenv('PYFED_DOMAIN', 'localhost'),
                    key_path=os.getenv('PYFED_KEY_PATH', 'keys'),
                    signature_ttl=int(os.getenv('PYFED_SIGNATURE_TTL', '300'))
                ),
                federation=FederationConfig(
                    domain=os.getenv('PYFED_DOMAIN', 'localhost'),
                    shared_inbox=os.getenv('PYFED_SHARED_INBOX', 'true').lower() == 'true',
                    delivery_timeout=int(os.getenv('PYFED_DELIVERY_TIMEOUT', '30')),
                    verify_ssl=os.getenv('PYFED_VERIFY_SSL', 'true').lower() == 'true'
                ),
                media=MediaConfig(
                    upload_path=os.getenv('PYFED_UPLOAD_PATH', 'uploads'),
                    max_size=int(os.getenv('PYFED_MAX_UPLOAD_SIZE', '10000000'))
                ),
                debug=os.getenv('PYFED_DEBUG', 'false').lower() == 'true'
            )
        except Exception as e:
            raise ConfigError(f"Failed to load config from env: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'domain': self.domain,
            'storage': {
                'provider': self.storage.provider,
                'database': asdict(self.storage.database)
            },
            'security': asdict(self.security),
            'federation': asdict(self.federation),
            'media': asdict(self.media),
            'debug': self.debug
        }

    def save(self, path: str) -> None:
        """Save configuration to file."""
        try:
            data = self.to_dict()
            with open(path, 'w') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")
