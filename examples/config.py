"""
Configuration for example servers.
"""

CONFIG = {
    "domain": "b055-197-211-61-144.ngrok-free.app",  # This should match the domain you're interacting with on Mastodon
    "user": "testuser",  # This should match the username you're interacting with on Mastodon
    "keys_path": "example_keys",
    "port": 8880,
    # # Storage configuration
    # "storage": {
    #     "backend": "sqlite",  # Can be postgresql, sqlite, mongodb, or redis
    #     "database_url": "sqlite:///activitypub.db",
    #     "cache_enabled": True,
    #     "cache_ttl": 3600  # Cache TTL in seconds
    # }
}