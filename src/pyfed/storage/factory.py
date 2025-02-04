from typing import Dict, Any, Type
from .backend import StorageBackend, LocalStorageBackend
from .s3 import S3StorageBackend

class StorageFactory:
    """Factory for creating storage backend instances."""
    
    _backends = {
        'local': LocalStorageBackend,
        's3': S3StorageBackend
    }
    
    @classmethod
    def register_backend(cls, name: str, backend_class: Type[StorageBackend]) -> None:
        """Register a new storage backend type.
        
        Args:
            name: Name to register the backend under
            backend_class: The backend class to register
        """
        cls._backends[name] = backend_class
        
    @classmethod
    async def create_backend(cls, backend_type: str, config: Dict[str, Any]) -> StorageBackend:
        """Create and initialize a storage backend instance.
        
        Args:
            backend_type: Type of backend to create ('local' or 's3')
            config: Configuration dictionary for the backend
            
        Returns:
            StorageBackend: Initialized storage backend instance
            
        Raises:
            ValueError: If backend_type is not recognized
        """
        if backend_type not in cls._backends:
            raise ValueError(f"Unknown storage backend type: {backend_type}")
            
        backend = cls._backends[backend_type]()
        await backend.initialize(config)
        return backend
