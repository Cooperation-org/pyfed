"""
Enhanced key management with rotation support.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
import aiofiles
import asyncio
import sys
from pathlib import Path

from ..utils.exceptions import KeyManagementError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class KeyRotation:
    """Key rotation configuration."""
    def __init__(self,
                 rotation_interval: int = 30,  # days
                 key_overlap: int = 2,  # days
                 key_size: int = 2048):
        self.rotation_interval = rotation_interval
        self.key_overlap = key_overlap
        self.key_size = key_size

class KeyPair:
    """Key pair with metadata."""
    def __init__(self,
                 private_key: RSAPrivateKey,
                 public_key: RSAPublicKey,
                 created_at: datetime,
                 expires_at: datetime,
                 key_id: str):
        self.private_key = private_key
        self.public_key = public_key
        self.created_at = created_at
        self.expires_at = expires_at
        self.key_id = key_id

class KeyManager:
    """Enhanced key management with rotation."""

    def __init__(
        self,
        domain: str,
        keys_path: str,
        rotation_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize key manager."""
        self.domain = domain
        self.keys_path = Path(keys_path)
        self.rotation_config = rotation_config or KeyRotation()
        self.active_keys: Dict[str, KeyPair] = {}
        self._rotation_task = None

    async def initialize(self) -> None:
        """Initialize key manager."""
        try:
            logger.info(f"Initializing key manager with path: {self.keys_path}")
            
            # Create keys directory
            self.keys_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created keys directory")
            
            # Load existing keys
            await self._load_existing_keys()
            logger.info(f"Loaded {len(self.active_keys)} existing keys")
            
            # Generate initial keys if none exist
            if not self.active_keys:
                logger.info("No active keys found, generating new key pair")
                await self.generate_key_pair()
                logger.info(f"Generated new key pair, total active keys: {len(self.active_keys)}")
            
            # Start rotation task
            self._rotation_task = asyncio.create_task(self._key_rotation_loop())
            logger.info("Started key rotation task")
            
        except Exception as e:
            logger.error(f"Failed to initialize key manager: {e}")
            raise KeyManagementError(f"Key manager initialization failed: {e}")

    async def  generate_key_pair(self) -> KeyPair:
        """Generate new key pair."""
        try:
            logger.info("Generating new key pair")
            # Generate keys
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.rotation_config.key_size
            )
            public_key = private_key.public_key()
            
            # Set validity period
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(days=self.rotation_config.rotation_interval)
            
            # Generate key ID (for HTTP use)
            timestamp = int(created_at.timestamp())
            key_id = f"https://{self.domain}/keys/{timestamp}"

            logger.debug(f"Key ID generated: {key_id}")
            
            # Generate safe file path (for storage)
            safe_timestamp = str(int(created_at.timestamp()))
            safe_domain = self.domain.replace(':', '_').replace('/', '_').replace('.', '_')
            safe_path = f"{safe_domain}_{safe_timestamp}"
            
            logger.info(f"Generated key ID: {key_id}")
            logger.info(f"Safe path: {safe_path}")
            
            # Create key pair
            key_pair = KeyPair(
                private_key=private_key,
                public_key=public_key,
                created_at=created_at,
                expires_at=expires_at,
                key_id=key_id
            )
            
            # Save keys with safe path
            await self._save_key_pair(key_pair, safe_path)
            logger.info("Saved key pair to disk")
            
            # Add to active keys
            self.active_keys[key_id] = key_pair
            logger.info(f"Added key pair to active keys. Total active keys: {len(self.active_keys)}")
            
            return key_pair
            
        except Exception as e:
            logger.error(f"Failed to generate key pair: {e}")
            raise KeyManagementError(f"Key generation failed: {e}")

    async def rotate_keys(self) -> None:
        """Perform key rotation."""
        try:
            logger.info("Starting key rotation")
            
            # Generate new key pair
            new_pair = await self.generate_key_pair()
            logger.info(f"Generated new key pair: {new_pair.key_id}")
            
            # Remove expired keys
            now = datetime.utcnow()
            expired = [
                key_id for key_id, pair in self.active_keys.items()
                if pair.expires_at < now - timedelta(days=self.rotation_config.key_overlap)
            ]
            
            for key_id in expired:
                await self._archive_key_pair(self.active_keys[key_id])
                del self.active_keys[key_id]
                logger.info(f"Archived expired key: {key_id}")
            
            # Announce new key to federation
            await self._announce_key_rotation(new_pair)
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise KeyManagementError(f"Key rotation failed: {e}")

    async def get_active_key(self) -> KeyPair:
        """Get the most recent active key."""
        if not self.active_keys:
            raise KeyManagementError("No active keys available")
            
        # Return most recently created key
        return max(
            self.active_keys.values(),
            key=lambda k: k.created_at
        )

    async def get_public_key_pem(self, username: str) -> str:
        """Get the public key in PEM format for a user."""
        active_key = await self.get_active_key()
        return active_key.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    async def verify_key(self, key_id: str, domain: str) -> bool:
        """Verify a key's validity."""
        try:
            # Check if key is one of our active keys
            if key_id in self.active_keys:
                key_pair = self.active_keys[key_id]
                return datetime.utcnow() <= key_pair.expires_at
                
            # For external keys, verify with their server
            # Implementation for external key verification
            return False
            
        except Exception as e:
            logger.error(f"Key verification failed: {e}")
            return False

    async def _load_existing_keys(self) -> None:
        """Load existing keys from disk."""
        try:
            # Recursively search for all json files
            for key_file in self.keys_path.rglob("*.json"):
                logger.info(f"Found key metadata file: {key_file}")
                async with aiofiles.open(key_file, 'r') as f:
                    metadata = json.loads(await f.read())
                    
                # Get the private key path from the same directory as the metadata
                private_key_path = key_file.parent / f"{key_file.stem}_private.pem"
                logger.info(f"Looking for private key at: {private_key_path}")
                
                if not private_key_path.exists():
                    logger.warning(f"Private key not found at {private_key_path}")
                    continue

                async with aiofiles.open(private_key_path, 'rb') as f:
                    private_key = serialization.load_pem_private_key(
                        await f.read(),
                        password=None
                    )
                
                # Create key pair
                key_pair = KeyPair(
                    private_key=private_key,
                    public_key=private_key.public_key(),
                    created_at=datetime.fromisoformat(metadata['created_at']),
                    expires_at=datetime.fromisoformat(metadata['expires_at']),
                    key_id=metadata['key_id']
                )
                
                # Add to active keys if not expired
                if datetime.utcnow() <= key_pair.expires_at:
                    self.active_keys[key_pair.key_id] = key_pair
                    logger.info(f"Loaded active key: {key_pair.key_id}")
                else:
                    logger.info(f"Skipping expired key: {key_pair.key_id}")
                    
        except Exception as e:
            logger.error(f"Failed to load existing keys: {e}")
            raise KeyManagementError(f"Failed to load existing keys: {e}")

    async def _save_key_pair(self, key_pair: KeyPair, safe_path: str) -> None:
        """Save key pair to disk."""
        try:
            # Save private key
            private_key_path = self.keys_path / f"{safe_path}_private.pem"
            private_pem = key_pair.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            async with aiofiles.open(private_key_path, 'wb') as f:
                await f.write(private_pem)
            
            # Save public key
            public_key_path = self.keys_path / f"{safe_path}_public.pem"
            public_pem = key_pair.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            async with aiofiles.open(public_key_path, 'wb') as f:
                await f.write(public_pem)
            
            # Save metadata
            metadata = {
                'key_id': key_pair.key_id,
                'created_at': key_pair.created_at.isoformat(),
                'expires_at': key_pair.expires_at.isoformat(),
                'safe_path': safe_path
            }
            metadata_path = self.keys_path / f"{safe_path}.json"
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata))
                
        except Exception as e:
            logger.error(f"Failed to save key pair: {e}")
            raise KeyManagementError(f"Failed to save key pair: {e}")

    async def _archive_key_pair(self, key_pair: KeyPair) -> None:
        """Archive an expired key pair."""
        try:
            archive_dir = self.keys_path / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Move key files to archive
            for ext in ['_private.pem', '_public.pem', '.json']:
                src = self.keys_path / f"{key_pair.key_id}{ext}"
                dst = archive_dir / f"{key_pair.key_id}{ext}"
                if src.exists():
                    src.rename(dst)
                    
        except Exception as e:
            logger.error(f"Failed to archive key pair: {e}")
            raise KeyManagementError(f"Failed to archive key pair: {e}")

    async def _announce_key_rotation(self, key_pair: KeyPair) -> None:
        """Announce new key to federation."""
        # Implementation for announcing key rotation to federation
        pass

    async def _key_rotation_loop(self) -> None:
        """Background task for key rotation."""
        while True:
            try:
                # Check for keys needing rotation
                now = datetime.utcnow()
                for key_pair in self.active_keys.values():
                    if key_pair.expires_at <= now + timedelta(days=1):
                        await self.rotate_keys()
                        break
                        
                # Sleep for a day
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Key rotation loop error: {e}")
                await asyncio.sleep(3600)  # Retry in an hour

    async def close(self) -> None:
        """Clean up resources."""
        if self._rotation_task:
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass

    async def get_active_private_key(self) -> RSAPrivateKey:
        """Get the most recent active private key."""
        if not self.active_keys:
            raise KeyManagementError("No active keys available")
        
        # Return the private key of the most recently created key
        most_recent_key = max(
            self.active_keys.values(),
            key=lambda k: k.created_at
        )
        return most_recent_key.private_key
