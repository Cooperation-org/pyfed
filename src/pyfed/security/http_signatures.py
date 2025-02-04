"""
security/http_signatures.py
Enhanced HTTP Signatures implementation.

Implements HTTP Signatures (draft-cavage-http-signatures) with:
- Key management
- Signature caching
- Request verification
- Performance optimization
"""

from typing import Dict, Any, Optional, List, Union
import base64
from unittest.mock import Mock
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib
from ..serializers.json_serializer import ActivityPubSerializer

from ..utils.exceptions import SignatureError
from ..utils.logging import get_logger
from ..cache.memory_cache import MemoryCache
from .key_management import KeyManager
# from ..config import CONFIG

logger = get_logger(__name__)

class SignatureCache:
    """Cache for HTTP signatures."""

    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache = MemoryCache(ttl)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached signature."""
        return await self.cache.get(key)

    async def set(self, key: str, value: Dict[str, Any]) -> None:
        """Cache signature."""
        await self.cache.set(key, value)

class HTTPSignatureVerifier:
    """Enhanced HTTP signature verification."""

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        private_key_path: str = "",
        public_key_path: str = "",
        key_id: Optional[str] = None
    ):
        """Initialize signature verifier."""
        self.key_manager = key_manager
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.key_id = key_id
        self.signature_cache = SignatureCache()
        self._test_now = None
        
        # Load keys only if paths are provided and no key_manager is present
        if not self.key_manager and (private_key_path or public_key_path):
            self.private_key = self._load_private_key()
            self.public_key = self._load_public_key()

    def set_test_time(self, test_time: datetime) -> None:
        """Set a fixed time for testing."""
        self._test_now = test_time

    def _load_private_key(self) -> rsa.RSAPrivateKey:
        """Load private key from file."""
        try:
            with open(self.private_key_path, 'rb') as f:
                key_data = f.read()
            return serialization.load_pem_private_key(
                key_data,
                password=None
            )
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise SignatureError(f"Failed to load private key: {e}")

    def _load_public_key(self) -> rsa.RSAPublicKey:
        """Load public key from file."""
        try:
            with open(self.public_key_path, 'rb') as f:
                key_data = f.read()
            return serialization.load_pem_public_key(key_data)
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise SignatureError(f"Failed to load public key: {e}")

    async def verify_request(self,
                             headers: Dict[str, str],
                             method: str = "POST",
                             path: str = "",
                             body: Optional[Dict[str, Any]] = None) -> bool:
        """Verify HTTP signature on request."""
        try:
            if 'signature' not in headers:
                logger.error("No signature header found")
                return False

            # Parse signature header
            sig_parts = {}
            for part in headers['signature'].split(','):
                if '=' not in part:
                    continue
                key, value = part.split('=', 1)
                sig_parts[key.strip()] = value.strip(' "')

            # Verify required signature components
            required_parts = ['keyId', 'headers', 'signature']
            if not all(part in sig_parts for part in required_parts):
                logger.error("Missing required signature parts")
                return False

            # Get signing key
            key_id = sig_parts['keyId']
            if not key_id:
                logger.error("No key ID in signature")
                return False

            # If body is provided and digest header exists, verify the digest
            if body is not None and 'digest' in headers:
                body_json = json.dumps(body, sort_keys=True)
                body_bytes = body_json.encode('utf-8')
                digest = hashlib.sha256(body_bytes).digest()
                expected_digest = f"SHA-256={base64.b64encode(digest).decode('utf-8')}"
                if headers['digest'] != expected_digest:
                    logger.error("Body digest verification failed")
                    return False

            # Build signing string
            signed_headers = sig_parts['headers'].split()
            lines = []
            for header in signed_headers:
                if header == '(request-target)':
                    lines.append(f"(request-target): {method.lower()} {path}")
                elif header in headers:
                    lines.append(f"{header}: {headers[header]}")
            signing_string = '\n'.join(lines)

            # Get public key
            public_key = await self._get_public_key(key_id)
            if not public_key:
                logger.error(f"Failed to get public key for {key_id}")
                return False

            # Verify signature
            try:
                signature = base64.b64decode(sig_parts['signature'])
                public_key.verify(
                    signature,
                    signing_string.encode(),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                return True
            except InvalidSignature:
                logger.error("Invalid signature")
                return False

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    async def sign_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        username: Optional[str] = None
    ) -> Dict[str, str]:
        """Sign HTTP request."""
        try:
            request_headers = headers.copy()
            
            # Add date if not present
            if 'date' not in request_headers:
                now = self._test_now if self._test_now is not None else datetime.utcnow()
                request_headers['date'] = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

            # Calculate digest first
            if body is not None:
                digest = self._generate_digest(body)
                request_headers['digest'] = digest
                logger.debug(f"Added digest header: {digest}")

            # Headers to sign (in specific order)
            headers_to_sign = ['(request-target)', 'host', 'date', 'digest']

            # Build signing string
            signing_string = self._build_signing_string(
                method,
                path,
                request_headers,
                headers_to_sign
            )
            
            logger.debug(f"Headers being signed: {headers_to_sign}")
            logger.debug(f"Signing string: {signing_string}")

            # Get private key
            if self.key_manager:
                private_key = await self.key_manager.get_active_private_key()
                active_key = await self.key_manager.get_active_key()
                if active_key:
                    key_id = active_key.key_id
                else:
                    raise SignatureError("No active key available")
            else:
                private_key = self.private_key
                key_id = self.key_id

            # Sign
            signature = private_key.sign(
                signing_string.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            # Build signature header
            signature_header = (
                f'keyId="{key_id}",'
                f'algorithm="rsa-sha256",'
                f'headers="{" ".join(headers_to_sign)}",'
                f'signature="{base64.b64encode(signature).decode()}"'
            )

            # Return headers with both Digest and Signature
            signed_headers = {
                **request_headers,
                'Signature': signature_header
            }
            
            logger.debug(f"Final headers: {signed_headers}")
            return signed_headers

        except Exception as e:
            logger.error(f"Request signing failed: {e}")
            raise SignatureError(f"Request signing failed: {e}")

    def _parse_signature_header(self, header: str) -> Dict[str, str]:
        """Parse HTTP signature header."""
        try:
            parts = {}
            for part in header.split(','):
                if '=' not in part:
                    continue
                key, value = part.split('=', 1)
                parts[key.strip()] = value.strip('"')
            
            required = ['keyId', 'algorithm', 'headers', 'signature']
            if not all(k in parts for k in required):
                raise SignatureError("Missing required signature parameters")
                
            return parts
        except Exception as e:
            raise SignatureError(f"Invalid signature header: {e}")

    def _verify_date(self, date_header: Optional[str]) -> bool:
        """
        Verify request date with clock skew handling.
        
        Allows 5 minutes of clock skew in either direction.
        """
        if not date_header:
            return False
            
        try:
            request_time = datetime.strptime(
                date_header,
                '%a, %d %b %Y %H:%M:%S GMT'
            ).replace(tzinfo=None)
            
            # Use test time if set, otherwise use current time
            now = self._test_now if self._test_now is not None else datetime.utcnow()
            now = now.replace(tzinfo=None)
            
            skew = timedelta(minutes=5)
            earliest = now - skew
            latest = now + skew
            
            logger.debug(
                f"Date verification: request_time={request_time}, "
                f"now={now}, earliest={earliest}, latest={latest}"
            )
            
            return earliest <= request_time <= latest
            
        except Exception as e:
            logger.debug(f"Date verification failed: {e}")
            return False

    def _build_signing_string(self,
                            method: str,
                            path: str,
                            headers: Dict[str, str],
                            signed_headers: List[str]) -> str:
        """Build string to sign."""
        try:
            lines = []
            # Convert headers to case-insensitive dictionary
            headers_lower = {k.lower(): v for k, v in headers.items()}
            
            for header in signed_headers:
                if header == '(request-target)':
                    lines.append(f"(request-target): {method.lower()} {path}")
                else:
                    header_lower = header.lower()
                    if header_lower not in headers_lower:
                        logger.error(f"Missing required header: {header}")
                        logger.error(f"Available headers: {list(headers_lower.keys())}")
                        raise SignatureError(f"Missing required header: {header}")
                    lines.append(f"{header_lower}: {headers_lower[header_lower]}")
                
            signing_string = '\n'.join(lines)
            logger.debug(f"Signing string: {signing_string}")
            return signing_string
            
        except Exception as e:
            logger.error(f"Failed to build signing string: {e}")
            logger.error(f"Headers: {headers}")
            logger.error(f"Signed headers: {signed_headers}")
            raise SignatureError(f"Failed to build signing string: {e}")

    def _generate_digest(self, body: Dict[str, Any]) -> str:
        """
        Generate digest header value for request body.
        
        Args:
            body: Request body as dictionary
            
        Returns:
            Digest header value
        """
        # Use standardized JSON serialization
        body_json = ActivityPubSerializer.to_json_string(body)
        body_bytes = body_json.encode('utf-8')
        
        # Calculate SHA-256 digest
        digest = hashlib.sha256(body_bytes).digest()
        digest_b64 = base64.b64encode(digest).decode('ascii')
        
        return f"SHA-256={digest_b64}"