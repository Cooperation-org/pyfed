"""
links.py
This module defines the Link types for ActivityPub.
These links are based on the ActivityStreams vocabulary.

For more information, see:
https://www.w3.org/TR/activitystreams-vocabulary/#link
"""

from pydantic import Field, HttpUrl, field_validator
from typing import Optional, List, Literal
from pyfed.serializers.json_serializer import ActivityPubBase

class APLink(ActivityPubBase):
    """
    Represents a Link in ActivityPub.
    
    A Link is an indirect, qualified reference to a resource identified by a URL.
    It can be used to represent a variety of connections between objects in the ActivityPub ecosystem.

    Properties:
        type (Literal["Link"]): The type of the object, always "Link" for this class.
        href (HttpUrl): The target resource pointed to by the link.
        rel (Optional[List[str]]): The relationship between the resource and the link.
        mediaType (Optional[str]): The MIME media type of the referenced resource.
        name (Optional[str]): A human-readable name for the link.
        hreflang (Optional[str]): The language of the referenced resource.
        height (Optional[int]): The height of the referenced resource in pixels.
        width (Optional[int]): The width of the referenced resource in pixels.
        preview (Optional[HttpUrl]): A link to a preview of the referenced resource.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#link
    Usage: https://www.w3.org/TR/activitypub/#object-without-create
    """
    type: Literal["Link"] = Field(default="Link", description="Indicates that this object represents a link")
    href: HttpUrl = Field(..., description="The target resource pointed to by the link")
    rel: Optional[List[str]] = Field(default=None, description="The relationship between the resource and the link")
    media_type: Optional[str] = Field(default=None, description="The MIME media type of the referenced resource")
    name: Optional[str] = Field(default=None, description="A human-readable name for the link")
    hreflang: Optional[str] = Field(default=None, description="The language of the referenced resource")
    height: Optional[int] = Field(default=None, description="The height of the referenced resource in pixels")
    width: Optional[int] = Field(default=None, description="The width of the referenced resource in pixels")
    preview: Optional[HttpUrl] = Field(default=None, description="A link to a preview of the referenced resource")

    @field_validator('media_type')
    def validate_media_type(cls, value):
        allowed_mimes = ["image/jpeg", "image/png", "application/json", "text/html", "video/mp4"]
        if value and not value in allowed_mimes:
            raise ValueError(f"Invalid MIME type: {value}")
        return value

class APMention(APLink):
    """
    Represents a Mention in ActivityPub.
    
    A Mention is a specialized Link that represents an @mention.
    It is typically used to reference another actor in the content of an object.

    Properties:
        type (Literal["Mention"]): The type of the object, always "Mention" for this class.
        href (HttpUrl): The URL of the mentioned actor.
        name (Optional[str]): The name or username of the mentioned actor.

    Inherits all other properties from APLink.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#mention
    Usage: https://www.w3.org/TR/activitypub/#mention
    """
    type: Literal["Mention"] = Field(default="Mention", description="Indicates that this object represents a mention")
