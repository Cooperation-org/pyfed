from abc import ABC, abstractmethod
from typing import Protocol, Optional, Union, BinaryIO, Dict, Any
from pathlib import Path
import asyncio
from datetime import datetime
import mimetypes
import os

class StorageBackend(Protocol):
    """Protocol defining the unified storage interface for both data and media."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the storage backend with configuration."""
        pass
    
    @abstractmethod
    async def store_file(self, 
                        file_data: Union[bytes, BinaryIO, Path], 
                        path: str,
                        mime_type: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a file in the storage backend.
        
        Args:
            file_data: The file data to store
            path: The path/key where the file should be stored
            mime_type: Optional MIME type of the file
            metadata: Optional metadata to store with the file
            
        Returns:
            str: The URI/path where the file was stored
        """
        pass
    
    @abstractmethod
    async def retrieve_file(self, path: str) -> bytes:
        """Retrieve a file from storage.
        
        Args:
            path: Path/key of the file to retrieve
            
        Returns:
            bytes: The file contents
        """
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> None:
        """Delete a file from storage.
        
        Args:
            path: Path/key of the file to delete
        """
        pass
    
    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists in storage.
        
        Args:
            path: Path/key to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get metadata for a stored file.
        
        Args:
            path: Path/key of the file
            
        Returns:
            Dict[str, Any]: File metadata including size, creation time, etc.
        """
        pass

class LocalStorageBackend:
    """Local filesystem implementation of StorageBackend."""
    
    def __init__(self):
        self.base_path: Optional[Path] = None
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize local storage with base path."""
        self.base_path = Path(config['base_path']).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def store_file(self, 
                        file_data: Union[bytes, BinaryIO, Path],
                        path: str,
                        mime_type: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a file in the local filesystem."""
        if self.base_path is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(file_data, bytes):
            full_path.write_bytes(file_data)
        elif isinstance(file_data, Path):
            if file_data.is_file():
                full_path.write_bytes(file_data.read_bytes())
        else:  # BinaryIO
            with full_path.open('wb') as f:
                f.write(file_data.read())
                
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + '.meta')
            meta_path.write_text(str(metadata))
            
        return str(full_path.relative_to(self.base_path))
    
    async def retrieve_file(self, path: str) -> bytes:
        """Retrieve a file from the local filesystem."""
        if self.base_path is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self.base_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        return full_path.read_bytes()
    
    async def delete_file(self, path: str) -> None:
        """Delete a file from the local filesystem."""
        if self.base_path is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self.base_path / path
        if full_path.exists():
            full_path.unlink()
            
        # Also delete metadata file if it exists
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        if meta_path.exists():
            meta_path.unlink()
            
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists in the local filesystem."""
        if self.base_path is None:
            raise RuntimeError("Storage backend not initialized")
            
        return (self.base_path / path).exists()
    
    async def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get metadata for a stored file."""
        if self.base_path is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self.base_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        stat = full_path.stat()
        metadata = {
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'mime_type': mimetypes.guess_type(str(full_path))[0]
        }
        
        # Check for additional metadata file
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        if meta_path.exists():
            try:
                additional_meta = eval(meta_path.read_text())  # Simple evaluation for demo
                metadata.update(additional_meta)
            except Exception:
                pass
                
        return metadata
