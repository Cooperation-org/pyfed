# """
# Storage package for ActivityPub data persistence.

# This package provides:
# - Abstract storage interfaces
# - Multiple storage backend implementations
# - Storage provider protocol
# """

from .base import SQLStorageBackend
# from .backends.postgresql import PostgreSQLStorage
# from .backends.mongodb import MongoDBStorageBackend
# from .backends.redis import RedisStorageBackend
# from .backends.sqlite import SQLiteStorage
# # Default storage backend
# DEFAULT_BACKEND = PostgreSQLStorage

# __all__ = [
#     'StorageBackend',
#     'StorageProvider',
#     'PostgreSQLStorage',
#     'MongoDBStorageBackend', 
#     'RedisStorageBackend',
#     'SQLiteStorage',
#     'DEFAULT_BACKEND'
# ]

# # Storage backend registry
# STORAGE_BACKENDS = {
#     'postgresql': PostgreSQLStorage,
#     'mongodb': MongoDBStorageBackend,
#     'redis': RedisStorageBackend,
#     'sqlite': SQLiteStorage
# }

def get_storage_backend(backend_type: str) -> type[SQLStorageBackend]:
    """Get storage backend class by type."""
    if backend_type not in STORAGE_BACKENDS:
        raise ValueError(f"Unknown storage backend: {backend_type}")
    return STORAGE_BACKENDS[backend_type]

# def register_backend(name: str, backend_class: type[StorageBackend]) -> None:
#     """Register a new storage backend."""
#     STORAGE_BACKENDS[name] = backend_class 