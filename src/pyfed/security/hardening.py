"""
Security hardening implementation.
"""

import base64
from typing import Dict, Any, Optional, List
import hashlib
import secrets
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

from ..utils.exceptions import SecurityError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class SecurityLevel(Enum):
    """Security level settings."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    STRICT = "strict"

@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    min_key_size: int
    key_rotation_days: int
    signature_max_age: int  # seconds
    require_digest: bool
    allowed_algorithms: List[str]
    blocked_ips: List[str]
    blocked_domains: List[str]
    request_timeout: int
    max_payload_size: int
    required_headers: List[str]

class SecurityHardening:
    """Security hardening implementation."""

    def __init__(self, level: SecurityLevel = SecurityLevel.ENHANCED):
        self.level = level
        self.policy = self._get_policy(level)
        self._nonce_cache = {}

    def _get_policy(self, level: SecurityLevel) -> SecurityPolicy:
        """Get security policy for level."""
        if level == SecurityLevel.BASIC:
            return SecurityPolicy(
                min_key_size=2048,
                key_rotation_days=90,
                signature_max_age=300,  # 5 minutes
                require_digest=False,
                allowed_algorithms=["rsa-sha256"],
                blocked_ips=[],
                blocked_domains=[],
                request_timeout=30,
                max_payload_size=5_000_000,  # 5MB
                required_headers=["date", "host"]
            )
        elif level == SecurityLevel.ENHANCED:
            return SecurityPolicy(
                min_key_size=4096,
                key_rotation_days=30,
                signature_max_age=120,  # 2 minutes
                require_digest=True,
                allowed_algorithms=["rsa-sha256", "rsa-sha512"],
                blocked_ips=[],
                blocked_domains=[],
                request_timeout=20,
                max_payload_size=1_000_000,  # 1MB
                required_headers=["date", "host", "digest"]
            )
        else:  # STRICT
            return SecurityPolicy(
                min_key_size=8192,
                key_rotation_days=7,
                signature_max_age=60,  # 1 minute
                require_digest=True,
                allowed_algorithms=["rsa-sha512"],
                blocked_ips=[],
                blocked_domains=[],
                request_timeout=10,
                max_payload_size=500_000,  # 500KB
                required_headers=["date", "host", "digest", "content-type"]
            )

    def validate_request(self,
                        headers: Dict[str, str],
                        body: Optional[str] = None,
                        remote_ip: Optional[str] = None) -> None:
        """
        Validate request security.
        
        Args:
            headers: Request headers
            body: Request body
            remote_ip: Remote IP address
            
        Raises:
            SecurityError if validation fails
        """
        try:
            # Check required headers
            for header in self.policy.required_headers:
                if header.lower() not in [k.lower() for k in headers]:
                    raise SecurityError(f"Missing required header: {header}")

            # Check signature algorithm
            sig_header = headers.get('signature', '')
            if 'algorithm=' in sig_header:
                algo = re.search(r'algorithm="([^"]+)"', sig_header)
                if algo and algo.group(1) not in self.policy.allowed_algorithms:
                    raise SecurityError(f"Unsupported signature algorithm: {algo.group(1)}")

            # Verify digest if required
            if self.policy.require_digest and body:
                if 'digest' not in headers:
                    raise SecurityError("Missing required digest header")
                if not self._verify_digest(headers['digest'], body):
                    raise SecurityError("Invalid digest")

            # Check payload size
            if body and len(body) > self.policy.max_payload_size:
                raise SecurityError("Payload too large")

            # Check IP/domain blocks
            if remote_ip and remote_ip in self.policy.blocked_ips:
                raise SecurityError("IP address blocked")

            # Verify nonce
            nonce = headers.get('nonce')
            if nonce and not self._verify_nonce(nonce):
                raise SecurityError("Invalid or reused nonce")

        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            raise SecurityError(f"Security validation failed: {e}")

    def _verify_digest(self, digest_header: str, body: str) -> bool:
        """Verify request digest."""
        try:
            algo, value = digest_header.split('=', 1)
            if algo.upper() == 'SHA-256':
                computed = hashlib.sha256(body.encode()).digest()
                return base64.b64encode(computed).decode() == value
            return False
        except:
            return False

    def _verify_nonce(self, nonce: str) -> bool:
        """Verify and track nonce."""
        now = datetime.utcnow()
        
        # Clean old nonces
        self._nonce_cache = {
            n: t for n, t in self._nonce_cache.items()
            if t > now - timedelta(minutes=5)
        }
        
        # Check if nonce used
        if nonce in self._nonce_cache:
            return False
            
        # Store nonce
        self._nonce_cache[nonce] = now
        return True

    def generate_nonce(self) -> str:
        """Generate secure nonce."""
        return secrets.token_urlsafe(32)

    def block_ip(self, ip: str) -> None:
        """Add IP to block list."""
        if ip not in self.policy.blocked_ips:
            self.policy.blocked_ips.append(ip)

    def block_domain(self, domain: str) -> None:
        """Add domain to block list."""
        if domain not in self.policy.blocked_domains:
            self.policy.blocked_domains.append(domain) 