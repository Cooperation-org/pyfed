"""
Video processing module for PyFed.
"""

from typing import Dict, Any, Optional, Tuple, BinaryIO
import asyncio
from pathlib import Path
import tempfile
import os
import ffmpeg
from moviepy.editor import VideoFileClip
import io
from PIL import Image
import magic

from ..utils.exceptions import MediaError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class VideoProcessor:
    """Handle video processing operations."""
    
    SUPPORTED_FORMATS = {
        'video/mp4': '.mp4',
        'video/webm': '.webm',
        'video/ogg': '.ogv',
        'video/quicktime': '.mov',
    }
    
    MAX_THUMBNAIL_SIZE = (1280, 720)  # 720p
    THUMBNAIL_QUALITY = 85
    
    @classmethod
    async def process_video(cls,
                          video_data: Union[bytes, BinaryIO, Path],
                          mime_type: Optional[str] = None) -> Dict[str, Any]:
        """Process video file and extract metadata.
        
        Args:
            video_data: Raw video data or file-like object
            mime_type: Optional MIME type of the video
            
        Returns:
            Dict containing video metadata and preview
        """
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            if isinstance(video_data, bytes):
                temp_file.write(video_data)
            elif isinstance(video_data, Path):
                temp_file.write(video_data.read_bytes())
            else:
                temp_file.write(video_data.read())
            temp_path = temp_file.name
            
        try:
            # Get video information using ffmpeg
            probe = await asyncio.to_thread(
                ffmpeg.probe,
                temp_path
            )
            
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            # Generate thumbnail
            thumbnail = await cls.generate_thumbnail(temp_path)
            
            metadata = {
                'duration': float(probe['format'].get('duration', 0)),
                'width': int(video_info.get('width', 0)),
                'height': int(video_info.get('height', 0)),
                'codec': video_info.get('codec_name', ''),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'thumbnail': thumbnail,
                'size': os.path.getsize(temp_path)
            }
            
            return metadata
            
        except Exception as e:
            raise MediaError(f"Failed to process video: {str(e)}") from e
            
        finally:
            os.unlink(temp_path)
    
    @classmethod
    async def generate_thumbnail(cls, video_path: str, time_offset: float = 1.0) -> bytes:
        """Generate a thumbnail from the video.
        
        Args:
            video_path: Path to video file
            time_offset: Time offset in seconds for thumbnail extraction
            
        Returns:
            bytes: Thumbnail image data in JPEG format
        """
        try:
            # Extract frame using ffmpeg
            out, _ = (
                ffmpeg
                .input(video_path, ss=time_offset)
                .filter('scale', cls.MAX_THUMBNAIL_SIZE[0], cls.MAX_THUMBNAIL_SIZE[1])
                .output('pipe:', format='image2', vframes=1)
                .run(capture_stdout=True)
            )
            
            # Convert to PIL Image and optimize
            image = Image.open(io.BytesIO(out))
            output = io.BytesIO()
            image.save(output,
                      format='JPEG',
                      quality=cls.THUMBNAIL_QUALITY,
                      optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            raise MediaError(f"Failed to generate thumbnail: {str(e)}") from e
    
    @classmethod
    async def validate_video(cls, file_data: Union[bytes, BinaryIO, Path]) -> Tuple[bool, str]:
        """Validate video file format and content.
        
        Args:
            file_data: Video file data
            
        Returns:
            Tuple[bool, str]: (is_valid, mime_type)
        """
        if isinstance(file_data, (bytes, BinaryIO)):
            mime = magic.from_buffer(
                file_data if isinstance(file_data, bytes) else file_data.read(2048),
                mime=True
            )
        else:
            mime = magic.from_file(str(file_data), mime=True)
            
        is_valid = mime in cls.SUPPORTED_FORMATS
        return is_valid, mime
