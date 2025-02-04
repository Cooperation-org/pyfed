"""
Media attachment handling implementation.
"""

from typing import Dict, Any, Optional, List, Union, BinaryIO
import aiohttp
import mimetypes
import hashlib
from pathlib import Path
import magic
from PIL import Image
import asyncio
import blurhash
import io
import mutagen
from mutagen.easyid3 import EasyID3
from pydub import AudioSegment
import numpy as np
import base64
from .video import VideoProcessor

from ..utils.exceptions import MediaError
from ..utils.logging import get_logger
from ..storage.backend import StorageBackend, LocalStorageBackend

logger = get_logger(__name__)

class MediaHandler:
    """Handle media attachments."""

    def __init__(self,
                 storage_backend: Optional[StorageBackend] = None,
                 max_size: int = 50 * 1024 * 1024,  # 50MB default
                 allowed_types: Optional[List[str]] = None):
        self.storage = storage_backend or LocalStorageBackend()
        self.max_size = max_size
        self.allowed_types = allowed_types or [
            'image/jpeg',
            'image/png',
            'image/gif',
            'video/mp4',
            'audio/mpeg',
            'audio/mp3',
            'audio/ogg',
            'audio/wav',
            'audio/flac',
            'audio/aac'
        ]

    async def process_attachment(self,
                               url: str,
                               description: Optional[str] = None) -> Dict[str, Any]:
        """
        Process media attachment.
        
        Args:
            url: Media URL
            description: Media description
            
        Returns:
            Processed attachment object
        """
        try:
            # Download media
            content = await self._download_media(url)
            
            # Validate media
            mime_type = magic.from_buffer(content, mime=True)
            if mime_type not in self.allowed_types:
                raise MediaError(f"Unsupported media type: {mime_type}")
                
            if len(content) > self.max_size:
                raise MediaError("Media too large")
            
            # Generate filename
            file_hash = hashlib.sha256(content).hexdigest()
            ext = mimetypes.guess_extension(mime_type) or ''
            filename = f"{file_hash}{ext}"
            
            # Save file using storage backend
            file_url = await self.storage.save(filename, content)
            
            # Process media based on type
            media_info = {}
            if mime_type.startswith('image/'):
                image = Image.open(io.BytesIO(content))
                media_info = {
                    'width': image.width,
                    'height': image.height,
                    'blurhash': await self._generate_blurhash(image),
                    'thumbnails': await self._generate_thumbnails(image, filename)
                }
            elif mime_type.startswith('audio/'):
                media_info = await self._process_audio(content, filename)
            elif mime_type.startswith('video/'):
                media_info = await self._process_video(content, mime_type)
            
            return {
                "type": "Document",
                "mediaType": mime_type,
                "url": file_url,
                "name": description or filename,
                **media_info
            }
            
        except Exception as e:
            logger.error(f"Failed to process attachment: {e}")
            raise MediaError(f"Failed to process attachment: {e}")

    async def _download_media(self, url: str) -> bytes:
        """Download media from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise MediaError(f"Failed to download media: {response.status}")
                    return await response.read()
        except Exception as e:
            raise MediaError(f"Failed to download media: {e}")

    async def _generate_thumbnails(self, image: Image.Image, original_filename: str) -> Dict[str, Dict[str, Any]]:
        """Generate image thumbnails."""
        thumbnails = {}
        sizes = [(320, 320), (640, 640)]
        
        try:
            for width, height in sizes:
                thumb = image.copy()
                thumb.thumbnail((width, height))
                
                # Convert to bytes
                thumb_bytes = io.BytesIO()
                thumb.save(thumb_bytes, format='JPEG', quality=85)
                thumb_bytes.seek(0)
                
                # Generate thumbnail filename
                thumb_hash = hashlib.sha256(f"{original_filename}_{width}x{height}".encode()).hexdigest()
                thumb_filename = f"thumb_{width}x{height}_{thumb_hash}.jpg"
                
                # Save thumbnail using storage backend
                thumb_url = await self.storage.save(thumb_filename, thumb_bytes.getvalue())
                
                thumbnails[f"{width}x{height}"] = {
                    "url": thumb_url,
                    "width": thumb.width,
                    "height": thumb.height
                }
            
            return thumbnails
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnails: {e}")
            return {}

    async def _generate_blurhash(self, image: Image.Image) -> str:
        """Generate blurhash for image."""
        try:
            # Convert image to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate blurhash
            return blurhash.encode(
                image,
                x_components=4,
                y_components=3
            )
        except Exception as e:
            logger.error(f"Failed to generate blurhash: {e}")
            return None

    async def _process_audio(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process audio file and extract metadata."""
        try:
            # Save temporary file for audio processing
            temp_file = io.BytesIO(content)
            temp_file.name = filename  # Required for mutagen
            
            # Extract metadata
            audio = mutagen.File(temp_file)
            if audio is None:
                return {}
            
            # Get basic metadata
            metadata = {
                'duration': int(audio.info.length),
                'bitrate': int(audio.info.bitrate),
                'channels': getattr(audio.info, 'channels', None),
                'sample_rate': getattr(audio.info, 'sample_rate', None)
            }
            
            # Try to get ID3 tags if available
            try:
                if isinstance(audio, EasyID3) or hasattr(audio, 'tags'):
                    tags = audio.tags or {}
                    metadata.update({
                        'title': str(tags.get('title', [''])[0]),
                        'artist': str(tags.get('artist', [''])[0]),
                        'album': str(tags.get('album', [''])[0]),
                        'genre': str(tags.get('genre', [''])[0])
                    })
            except Exception as e:
                logger.warning(f"Failed to extract audio tags: {e}")
            
            # Generate waveform
            try:
                waveform_data = await self._generate_waveform(content)
                metadata['waveform'] = waveform_data
            except Exception as e:
                logger.warning(f"Failed to generate waveform: {e}")
            
            # Generate audio preview
            try:
                preview_url = await self._generate_audio_preview(content, filename)
                metadata['preview_url'] = preview_url
            except Exception as e:
                logger.warning(f"Failed to generate audio preview: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
            return {}

    async def _generate_waveform(self, content: bytes, num_points: int = 100) -> str:
        """Generate waveform data for audio visualization."""
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(content))
            
            # Convert to mono and get raw data
            samples = np.array(audio.get_array_of_samples())
            
            # Resample to desired number of points
            samples = np.array_split(samples, num_points)
            waveform = [float(abs(chunk).mean()) for chunk in samples]
            
            # Normalize to 0-1 range
            max_val = max(waveform)
            if max_val > 0:
                waveform = [val/max_val for val in waveform]
            
            # Convert to base64 for efficient transfer
            waveform_bytes = np.array(waveform, dtype=np.float32).tobytes()
            return base64.b64encode(waveform_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to generate waveform: {e}")
            return None

    async def _generate_audio_preview(self, content: bytes, filename: str, duration: int = 30) -> Optional[str]:
        """Generate a short preview of the audio file."""
        try:
            # Load audio
            audio = AudioSegment.from_file(io.BytesIO(content))
            
            # Take first 30 seconds
            preview_duration = min(duration * 1000, len(audio))
            preview = audio[:preview_duration]
            
            # Convert to MP3 format
            preview_bytes = io.BytesIO()
            preview.export(preview_bytes, format='mp3', bitrate='128k')
            preview_bytes.seek(0)
            
            # Generate preview filename
            preview_hash = hashlib.sha256(f"preview_{filename}".encode()).hexdigest()
            preview_filename = f"preview_{preview_hash}.mp3"
            
            # Save preview using storage backend
            preview_url = await self.storage.save(preview_filename, preview_bytes.getvalue())
            
            return preview_url
            
        except Exception as e:
            logger.error(f"Failed to generate audio preview: {e}")
            return None

    async def _process_video(self,
                           file_data: Union[bytes, BinaryIO, Path],
                           mime_type: str) -> Dict[str, Any]:
        """Process video file and extract metadata."""
        is_valid, detected_mime = await VideoProcessor.validate_video(file_data)
        if not is_valid:
            raise MediaError(f"Invalid or unsupported video format: {detected_mime}")
            
        metadata = await VideoProcessor.process_video(file_data, mime_type)
        return metadata