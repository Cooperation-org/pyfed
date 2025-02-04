# PyFed Security Guide

## Overview
PyFed implements comprehensive security measures for ActivityPub federation, including:
- HTTP Signatures
- Key Management
- OAuth2 Authentication
- Request Validation
- Rate Limiting

## Key Management

### Key Generation and Storage
PyFed uses RSA key pairs for signing ActivityPub requests:

```python
from pyfed.security import KeyManager

key_manager = KeyManager(
    domain="example.com",
    keys_path="keys",
    rotation_config={
        "rotation_interval": 30,  # days
        "key_overlap": 2,        # days
        "key_size": 2048        # bits
    }
)

# Initialize key manager
await key_manager.initialize()
```

## Key Rotation

Keys are automatically rotated to maintain security:

- Default rotation interval: 30 days
- Overlap period: 2 days (to handle in-flight requests)
- Automatic archival of expired keys
- Federation announcement of new keys

## Key Storage Security

- Private keys are stored with proper permissions
- Keys are stored in PEM format
- Separate directories for active and archived keys
- Metadata stored alongside keys for tracking

## HTTP Signatures

### Request Signing
All outgoing ActivityPub requests are signed:

```python
from pyfed.security import HTTPSignatureVerifier

# Create signature verifier
verifier = HTTPSignatureVerifier(key_manager)

# Sign request
headers = await verifier.sign_request(
    method="POST",
    path="/inbox",
    headers={"Content-Type": "application/activity+json"},
    body=activity_data
)
```

### Signature Verification
#### Incoming requests are verified:

```python
# Verify request signature
is_valid = await verifier.verify_request(
    method=request.method,
    path=request.path,
    headers=request.headers,
    body=request.body
)
```

Signature Format
PyFed uses the standard HTTP Signatures format:

```bash
Signature: keyId="https://example.com/keys/1234",
          algorithm="rsa-sha256",
          headers="(request-target) host date digest",
          signature="base64..."
```

## OAuth2 Authentication
Token Generation
Client-to-server authentication using OAuth2:
```python
from pyfed.security import OAuth2Handler

oauth = OAuth2Handler(
    client_id="client_id",
    client_secret="client_secret",
    token_endpoint="https://example.com/oauth/token"
)

# Create token
token = await oauth.create_token(
    username="user",
    password="pass",
    scope="read write"
)
```

#### Token Verification
```python
# Verify token
try:
    payload = await oauth.verify_token(
        token="access_token",
        required_scope="write"
    )
except AuthenticationError as e:
    # Handle invalid token
    pass
```

#### Token Management
- Automatic token refresh
- Token caching
- Scope validation
- Token revocation

#### Request Validation
- Activity Validation
All incoming activities are validated:

```python
from pyfed.handlers import ActivityHandler

class CustomHandler(ActivityHandler):
    async def validate(self, activity):
        # Validate activity type
        if activity.get('type') != 'Create':
            raise ValidationError("Invalid activity type")
            
        # Validate required fields
        if 'object' not in activity:
            raise ValidationError("Missing object")
            
        # Validate permissions
        if not await self.can_create(activity['actor']):
            raise ValidationError("Unauthorized")
            
        # Validate content
        await self._validate_content(activity['object'])
```

#### Content Validation
- Media type validation
- Size limits
- Content scanning
- Malware detection

#### Rate Limiting
Configuration
```yaml
rate_limits:
  inbox:
    window: 3600  # seconds
    max_requests: 1000
  media:
    window: 3600
    max_requests: 100
    max_size: 10485760  # bytes
```

Implementation
```python
from pyfed.security import RateLimiter

limiter = RateLimiter(
    redis_url="redis://localhost",
    config=rate_limit_config
)

# Check rate limit
allowed = await limiter.check_limit(
    key="inbox",
    identifier=request.remote_addr
)
```

#### Best Practices

##### 1. Key Management
- Regularly rotate keys (30 days recommended)
- Securely store private keys
- Monitor key usage and expiration
- Implement key backup procedures

##### 2. Request Signing
Sign all outgoing requests
Verify all incoming signatures
Use strong algorithms (rsa-sha256)
Include relevant headers in signature

3. Authentication
Use OAuth2 for C2S authentication
Implement proper scope validation
Securely store client secrets
Regular token rotation

4. Content Security
Validate all incoming content
Implement upload limits
Scan for malware
Sanitize user content

5. Rate Limiting
Implement per-endpoint limits
Use sliding windows
Account for bursts
Monitor abuse patterns

### Security Headers
#### Recommended Headers
```python
security_headers = {
    'Content-Security-Policy': "default-src 'self'",
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
}
```

### Monitoring and Logging
#### Security Events
```python
# Configure security logging
logging.config.dictConfig({
    'handlers': {
        'security': {
            'class': 'logging.FileHandler',
            'filename': 'security.log',
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'pyfed.security': {
            'handlers': ['security'],
            'level': 'INFO'
        }
    }
})
```

#### Metrics Collection
- Failed authentication attempts
- Signature verification failures
- Rate limit violations
- Key rotation events

#### Error Handling
#### Security Exceptions
PyFed provides specific security exceptions:
- KeyManagementError
- SignatureError
- AuthenticationError
- ValidationError
- RateLimitError

Example Error Handling
```python
try:
    await verifier.verify_signature(request)
except SignatureError as e:
    logger.warning(f"Signature verification failed: {e}")
    return JsonResponse(
        {"error": "Invalid signature"},
        status=401
    )
```

See Also
[Configuration Guide](configuration.md)
[API Reference](api/)
[Architecture Guide](architecture.md)