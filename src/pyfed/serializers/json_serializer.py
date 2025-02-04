"""
JSON serializer for ActivityPub objects.
"""

from typing import Any, Dict, Union, List, Optional, Type, get_origin, get_args
from datetime import datetime, timezone
import json
import re
from pydantic import BaseModel, AnyUrl, HttpUrl
from pydantic_core import Url

def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def is_url_field(field_name: str) -> bool:
    """Check if field name suggests it's a URL."""
    url_indicators = [
        'url', 'href', 'id', 'inbox', 'outbox', 'following',
        'followers', 'liked', 'icon', 'image', 'avatar',
        'endpoints', 'featured', 'streams'
    ]
    return any(indicator in field_name.lower() for indicator in url_indicators)

class ActivityPubSerializer:
    """ActivityPub serializer implementation."""
    
    @staticmethod
    def _process_value(value: Any, field_name: str = "", depth: int = 0) -> Any:
        """
        Process a single value for serialization.
        
        Args:
            value: Value to process
            field_name: Name of the field being processed
            depth: Current recursion depth
            
        Returns:
            Processed value
        """
        # Prevent infinite recursion
        if depth > 10:  # Maximum nesting depth
            return str(value)

        if value is None:
            return None

        # Handle BaseModel instances (nested objects)
        if isinstance(value, BaseModel):
            # Recursively serialize nested objects
            serialized = value.model_dump(exclude_none=True)
            return {
                to_camel_case(k): ActivityPubSerializer._process_value(v, k, depth + 1)
                for k, v in serialized.items()
            }

        # Handle URL types - using pydantic_core.Url instead of AnyUrl
        if isinstance(value, Url):
            return str(value)

        # Handle datetime
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()

        # Handle lists with potential nested objects
        if isinstance(value, list):
            return [
                ActivityPubSerializer._process_value(item, field_name, depth + 1)
                for item in value
            ]

        # Handle dictionaries with potential nested objects
        if isinstance(value, dict):
            return {
                to_camel_case(k): ActivityPubSerializer._process_value(v, k, depth + 1)
                for k, v in value.items()
            }

        # Convert string to URL if field name suggests it's a URL
        if isinstance(value, str) and is_url_field(field_name):
            if not value.startswith(('http://', 'https://')):
                value = f"https://{value}"
            return value

        return value

    @staticmethod
    def to_json_string(data: Dict[str, Any]) -> str:
        """
        Convert dictionary to JSON string with standardized formatting.
        
        Args:
            data: Dictionary to convert
            
        Returns:
            JSON string with consistent formatting
        """
        return json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=True,
            separators=(',', ':')
        )

    @staticmethod
    def serialize(obj: Any, include_context: bool = True) -> Dict[str, Any]:
        """
        Serialize object to dictionary.
        
        Args:
            obj: Object to serialize
            include_context: Whether to include @context
            
        Returns:
            Serialized dictionary
        """
        if not isinstance(obj, BaseModel):
            return ActivityPubSerializer._process_value(obj)

        # Process each field
        processed_data = ActivityPubSerializer._process_value(obj)
        
        # Add context if needed
        if include_context:
            processed_data["@context"] = ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"]
            
        return processed_data

    @staticmethod
    def _process_field_value(value: Any, field_type: Any) -> Any:
        """
        Process field value during deserialization.
        
        Args:
            value: Value to process
            field_type: Type annotation for the field
            
        Returns:
            Processed value
        """
        # Handle None values
        if value is None:
            return None

        # Handle nested BaseModel
        if hasattr(field_type, 'model_fields'):
            return ActivityPubSerializer.deserialize(value, field_type)

        # Handle lists
        origin = get_origin(field_type)
        if origin is list:
            args = get_args(field_type)
            if args and hasattr(args[0], 'model_fields'):
                return [
                    ActivityPubSerializer.deserialize(item, args[0])
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]

        # Handle dictionaries
        if origin is dict:
            key_type, val_type = get_args(field_type)
            if hasattr(val_type, 'model_fields'):
                return {
                    k: ActivityPubSerializer.deserialize(v, val_type)
                    if isinstance(v, dict)
                    else v
                    for k, v in value.items()
                }

        return value

    @staticmethod
    def deserialize(data: Union[str, Dict[str, Any]], model_class: Type[BaseModel]) -> BaseModel:
        """
        Deserialize data to object.
        
        Args:
            data: JSON string or dictionary to deserialize
            model_class: Class to deserialize into
            
        Returns:
            Deserialized object
        """
        # Handle JSON string input
        if isinstance(data, str):
            try:
                data_dict = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string")
        else:
            data_dict = data

        if not isinstance(data_dict, dict):
            raise ValueError("Data must be a dictionary or JSON string")

        # Make a copy of the data
        data_dict = dict(data_dict)
        
        # Remove context if present
        data_dict.pop('@context', None)
        
        # Convert keys from camelCase to snake_case and process values
        processed_data = {}
        for key, value in data_dict.items():
            if key == '@context':
                continue
                
            snake_key = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', key).lower()
            
            # Get field info from model
            field_info = model_class.model_fields.get(snake_key)
            if field_info is None:
                continue

            # Process the field value
            processed_value = ActivityPubSerializer._process_field_value(
                value, field_info.annotation
            )
            
            processed_data[snake_key] = processed_value

        # Use model_validate instead of direct construction
        return model_class.model_validate(processed_data)

class ActivityPubBase(BaseModel):
    """Base class for all ActivityPub objects."""
    
    def serialize(self, include_context: bool = True) -> Dict[str, Any]:
        """Serialize object to dictionary."""
        return ActivityPubSerializer.serialize(self, include_context)

    @classmethod
    def deserialize(cls, data: Union[str, Dict[str, Any]]) -> 'ActivityPubBase':
        """Deserialize dictionary to object."""
        return ActivityPubSerializer.deserialize(data, cls)

    class Config:
        """Pydantic config."""
        alias_generator = to_camel_case
        populate_by_alias = True
        extra = "allow"
        arbitrary_types_allowed = True
        populate_by_name = True

def to_json(obj: ActivityPubBase, **kwargs) -> str:
    """Convert object to JSON string."""
    return ActivityPubSerializer.to_json_string(ActivityPubSerializer.serialize(obj))

def from_json(json_str: str, model_class: Type[ActivityPubBase]) -> ActivityPubBase:
    """Convert JSON string to object."""
    return ActivityPubSerializer.deserialize(json_str, model_class)
