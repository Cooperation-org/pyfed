class ActivityPubException(Exception):
    """Base exception for ActivityPub-related errors."""

class ValidationError(ActivityPubException):
    """Raised when validation fails."""

class DeserializationError(ActivityPubException):
    """Raised when deserialization fails."""

class RemoteObjectFetchError(ActivityPubException):
    """Raised when fetching a remote object fails."""

class InvalidURLError(ValidationError):
    """Raised when an invalid URL is provided."""

class InvalidDateTimeError(ValidationError):
    """Raised when an invalid date/time is provided."""

class SignatureVerificationError(ActivityPubException):
    """Raised when signature verification fails."""
    pass

class SignatureError(ActivityPubException):
    """Raised when signature creation fails."""
    pass

class AuthenticationError(ActivityPubException):
    """Raised when authentication fails."""
    pass

class RateLimitExceeded(ActivityPubException):
    """Raised when rate limit is exceeded."""
    pass

class WebFingerError(ActivityPubException):
    """Raised when WebFinger lookup fails."""
    pass

class SecurityError(ActivityPubException):
    """Raised when security-related errors occur."""
    pass

class DeliveryError(ActivityPubException):
    """Raised when delivery fails."""
    pass

class FetchError(ActivityPubException):
    """Raised when fetching fails."""
    pass

class DiscoveryError(ActivityPubException):
    """Raised when discovery fails."""
    pass

class ResolutionError(ActivityPubException):
    """Raised when rosolving fails."""
    pass

class HandlerError(ActivityPubException):
    """Raised when handling fails"""
    pass

class RateLimitError(ActivityPubException):
    """Raised when rate limit is exceeded."""
    pass

class TokenError(ActivityPubException):
    """Raised when token-related errors occur."""
    pass

class OAuthError(ActivityPubException):
    """Raised when OAuth-related errors occur."""
    pass

class RateLimiterError(ActivityPubException):
    """Raised when rate limiter-related errors occur."""
    pass

class FetchError(ActivityPubException):
    """Raised when fetching fails."""
    pass

class StorageError(ActivityPubException):
    """Raised when storage-related errors occur."""
    pass    

class DiscoveryError(ActivityPubException):
    """Raised when discovery fails."""
    pass    

class ResolverError(ActivityPubException):
    """Raised when resolver-related errors occur."""
    pass    

class SignatureError(ActivityPubException):
    """Raised when signature-related errors occur."""
    pass

class SecurityValidatorError(ActivityPubException):
    """Raised when security validator-related errors occur."""
    pass

class DeliveryError(ActivityPubException):
    """Raised when delivery-related errors occur."""
    pass

class ResourceFetcherError(ActivityPubException):
    """Raised when resource fetcher-related errors occur."""
    pass    

class SecurityValidatorError(ActivityPubException):
    """Raised when security validator-related errors occur."""
    pass   

class WebFingerError(ActivityPubException):
    """Raised when WebFinger-related errors occur."""
    pass

class KeyManagementError(ActivityPubException):
    """Raised when key manager-related errors occur."""
    pass

class CollectionError(ActivityPubException):
    """Raised when collection-related errors occur."""
    pass

class ContentError(ActivityPubException):
    """Raised when content-related errors occur."""
    pass

class ContentHandlerError(ActivityPubException):
    """Raised when content handler-related errors occur."""
    pass

class CollectionHandlerError(ActivityPubException):
    """Raised when collection handler-related errors occur."""
    pass

class IntegrationError(ActivityPubException):
    """Raised when integration-related errors occur."""
    pass

class MiddlewareError(ActivityPubException):
    """Raised when middleware-related errors occur."""
    pass