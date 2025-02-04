from typing import Union, BinaryIO, Dict, Any, Optional
from pathlib import Path
import aioboto3
from datetime import datetime
import io
import mimetypes
import json

from .backend import StorageBackend

class S3StorageBackend:
    """S3-compatible storage backend implementation."""
    
    def __init__(self):
        self.session = None
        self.bucket = None
        self.prefix = None
        self.client = None
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize S3 storage with credentials and configuration."""
        self.session = aioboto3.Session(
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key')
        )
        self.bucket = config['bucket']
        self.prefix = config.get('prefix', '')
        self.endpoint_url = config.get('endpoint_url')  # For compatibility with other S3-compatible services
        
    async def _get_client(self):
        """Get or create S3 client."""
        if self.client is None:
            self.client = self.session.client('s3', endpoint_url=self.endpoint_url)
        return self.client
        
    def _get_full_path(self, path: str) -> str:
        """Get full S3 path including prefix."""
        return f"{self.prefix.rstrip('/')}/{path.lstrip('/')}" if self.prefix else path
        
    async def store_file(self,
                        file_data: Union[bytes, BinaryIO, Path],
                        path: str,
                        mime_type: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a file in S3 storage."""
        if self.session is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self._get_full_path(path)
        
        # Prepare the file data
        if isinstance(file_data, bytes):
            data = io.BytesIO(file_data)
        elif isinstance(file_data, Path):
            data = io.BytesIO(file_data.read_bytes())
        else:
            data = file_data
            
        # Prepare upload parameters
        upload_kwargs = {
            'Bucket': self.bucket,
            'Key': full_path,
            'Body': data
        }
        
        if mime_type:
            upload_kwargs['ContentType'] = mime_type
            
        if metadata:
            # S3 metadata must be strings
            upload_kwargs['Metadata'] = {
                k: str(v) for k, v in metadata.items()
            }
            
        async with await self._get_client() as client:
            await client.upload_fileobj(**upload_kwargs)
            
        return full_path
        
    async def retrieve_file(self, path: str) -> bytes:
        """Retrieve a file from S3 storage."""
        if self.session is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self._get_full_path(path)
        data = io.BytesIO()
        
        async with await self._get_client() as client:
            try:
                await client.download_fileobj(
                    Bucket=self.bucket,
                    Key=full_path,
                    Fileobj=data
                )
            except Exception as e:
                raise FileNotFoundError(f"File not found: {path}") from e
                
        return data.getvalue()
        
    async def delete_file(self, path: str) -> None:
        """Delete a file from S3 storage."""
        if self.session is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self._get_full_path(path)
        
        async with await self._get_client() as client:
            try:
                await client.delete_object(
                    Bucket=self.bucket,
                    Key=full_path
                )
            except Exception as e:
                # Ignore if file doesn't exist
                pass
                
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists in S3 storage."""
        if self.session is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self._get_full_path(path)
        
        async with await self._get_client() as client:
            try:
                await client.head_object(
                    Bucket=self.bucket,
                    Key=full_path
                )
                return True
            except:
                return False
                
    async def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get metadata for a stored file."""
        if self.session is None:
            raise RuntimeError("Storage backend not initialized")
            
        full_path = self._get_full_path(path)
        
        async with await self._get_client() as client:
            try:
                response = await client.head_object(
                    Bucket=self.bucket,
                    Key=full_path
                )
                
                metadata = {
                    'size': response['ContentLength'],
                    'created': response.get('LastModified'),
                    'mime_type': response.get('ContentType'),
                    'etag': response.get('ETag'),
                }
                
                # Include custom metadata if present
                if 'Metadata' in response:
                    metadata.update(response['Metadata'])
                    
                return metadata
                
            except Exception as e:
                raise FileNotFoundError(f"File not found: {path}") from e
