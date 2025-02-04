"""
objects.py
This module defines the core object types for ActivityPub.
These objects are based on the ActivityStreams vocabulary.

For more information, see:
https://www.w3.org/TR/activitystreams-vocabulary/
"""

from ..serializers.json_serializer import ActivityPubBase
from pydantic import Field, HttpUrl, field_validator, model_validator
from typing import Optional, List, Union, Literal, Dict
from datetime import datetime
from pyfed.models.links import APLink

class APObject(ActivityPubBase):
    """Base class for all ActivityPub objects.
    
    According to ActivityStreams 2.0 Core Types:
    https://www.w3.org/TR/activitystreams-core/#object

    Properties:
        id (HttpUrl): Unique identifier for the object.
        type (str): The type of the object.
        attachment (Optional[List[Union[str, 'APObject']]]): Files or objects attached.
        attributed_to (Optional[Union[str, 'APObject']]): Entity responsible for this object.
        audience (Optional[List[Union[str, 'APObject']]]): Intended audience.
        content (Optional[str]): The content/body of the object.
        context (Optional[Union[str, 'APObject']]): Context of the object.
        name (Optional[str]): Human-readable title.
        end_time (Optional[datetime]): When the object concludes.
        generator (Optional[Union[str, 'APObject']]): Application that generated this.
        icon (Optional[Union[str, 'APObject']]): Small image representation.
        image (Optional[Union[str, 'APObject']]): Larger image representation.
        in_reply_to (Optional[Union[str, HttpUrl, 'APObject']]): Object being replied to.
        location (Optional[Union[str, 'APObject']]): Physical or logical location.
        preview (Optional[Union[str, 'APObject']]): Preview of this object.
        published (Optional[datetime]): Publication timestamp.
        replies (Optional[Union[str, 'APObject']]): Collection of replies.
        start_time (Optional[datetime]): When the object begins.
        summary (Optional[str]): Brief description.
        tag (Optional[List[Union[str, Dict[str, str], 'APObject', 'APLink']]]): Associated tags.
        updated (Optional[datetime]): Last update timestamp.
        url (Optional[Union[HttpUrl, List[HttpUrl]]]): Link to the object.
        to (Optional[List[Union[str, HttpUrl]]]): Primary recipients.
        bto (Optional[List[Union[str, HttpUrl]]]): Private primary recipients.
        cc (Optional[List[Union[str, HttpUrl]]]): Secondary recipients.
        bcc (Optional[List[Union[str, HttpUrl]]]): Private secondary recipients.
        media_type (Optional[str]): MIME type of the object.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#object
    Usage: https://www.w3.org/TR/activitypub/#object
    """
    id: HttpUrl = Field(..., description="Unique identifier for the object")
    type: Literal["Object"] = Field(..., description="The type of the object")
    attachment: Optional[List[Union[str, 'APObject']]] = Field(default=None, description="Files attached to the object")
    attributed_to: Optional[Union[str, 'APObject']] = Field(default=None, description="Entity attributed to this object")
    audience: Optional[List[Union[str, 'APObject']]] = Field(default=None, description="Intended audience")
    content: Optional[str] = Field(default=None, description="The content of the object")
    context: Optional[Union[str, 'APObject']] = Field(default=None, description="Context of the object")
    name: Optional[str] = Field(default=None, description="The name/title of the object")
    end_time: Optional[datetime] = Field(default=None, description="End time of the object")
    generator: Optional[Union[str, 'APObject']] = Field(default=None, description="Application that generated the object")
    icon: Optional[Union[str, 'APObject']] = Field(default=None, description="Icon representing the object")
    image: Optional[Union[str, 'APObject']] = Field(default=None, description="Image representing the object")
    in_reply_to: Optional[Union[str, HttpUrl, 'APObject']] = Field(
        default=None, 
        description="Object this is in reply to"
    )
    location: Optional[Union[str, 'APObject']]= Field(default=None, description="Location associated with the object")
    preview: Optional[Union[str, 'APObject']]= Field(default=None, description="Preview of the object")
    published: Optional[datetime] = Field(default=None, description="Publication date")
    replies: Optional[Union[str, 'APObject']]= Field(default=None, description="Replies to this object")
    start_time: Optional[datetime] = Field(default=None, description="Start time of the object")
    summary: Optional[str] = Field(default=None, description="Summary of the object")
    tag: Optional[List[Union[str, Dict[str, str], 'APObject', 'APLink']]] = Field(
        default=None, 
        description="Tags associated with the object"
    )
    updated: Optional[datetime] = Field(default=None, description="Last update time")
    url: Optional[Union[HttpUrl, List[HttpUrl]]] = Field(default=None, description="URL of the object")
    to: Optional[List[Union[str, HttpUrl]]] = Field(default=None, description="Primary recipients")
    bto: Optional[List[Union[str, HttpUrl]]] = Field(default=None, description="Private primary recipients")
    cc: Optional[List[Union[str, HttpUrl]]] = Field(default=None, description="Secondary recipients")
    bcc: Optional[List[Union[str, HttpUrl]]] = Field(default=None, description="Private secondary recipients")
    media_type: Optional[str] = Field(default=None, description="MIME type")

    @field_validator('media_type')
    def validate_media_type(cls, value):
        allowed_mimes = ["image/jpeg", "image/png", "application/json", "text/html", "video/mp4"]
        if value and not value in allowed_mimes:
            raise ValueError(f"Invalid MIME type: {value}")
        return value

    def is_public(self) -> bool:
        """Check if the object is public."""
        public_address = "https://www.w3.org/ns/activitystreams#Public"
        return (
            (isinstance(self.to, list) and public_address in self.to) or
            (isinstance(self.cc, list) and public_address in self.cc)
        )

    def get_mentions(self) -> List[str]:
        """Extract mentions from the object's tags."""
        if not self.tag:
            return []
        return [
            tag['href'] 
            for tag in self.tag 
            if isinstance(tag, dict) and tag.get('type') == "Mention"
        ]

    def __str__(self):
        return str(self.id)

class APEvent(APObject):
    """Event object as defined in ActivityStreams 2.0.
    
    An Event represents any kind of event that can occur, such as a concert,
    a meeting, or a conference.

    Properties:
        type (Literal["Event"]): Always set to "Event".
        start_time (Optional[datetime]): When the event begins.
        end_time (Optional[datetime]): When the event concludes.
        location (Optional['APPlace']): Where the event takes place.

    Validation:
        - end_time must be after start_time if both are provided
        - Inherits all validation from APObject

    https://www.w3.org/TR/activitystreams-vocabulary/#event
    """
    type: Literal["Event"] = Field(default="Event", description="Indicates that this object represents an event")
    start_time: Optional[datetime] = Field(default=None, description="The start time of the event")
    end_time: Optional[datetime] = Field(default=None, description="The end time of the event")
    location: Optional['APPlace'] = Field(default=None, description="The location of the event")

    @model_validator(mode='after')
    def validate_end_time(self) -> 'APEvent':
        """Validate that end_time is after start_time if both are provided."""
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError('end_time must be after start_time')
        return self

class APPlace(APObject):
    """Place object as defined in ActivityStreams 2.0.
    
    A Place represents a physical or logical location. It can be used to represent
    a geographic location, a venue, or any other kind of place.

    Properties:
        type (Literal["Place"]): Always set to "Place".
        accuracy (Optional[float]): The accuracy of the coordinates (in meters).
        altitude (Optional[float]): The altitude of the place (in meters).
        latitude (Optional[float]): The latitude (-90 to 90).
        longitude (Optional[float]): The longitude (-180 to 180).
        radius (Optional[float]): The radius of uncertainty.
        units (Optional[str]): The units for the radius (e.g., 'cm', 'feet', 'km').

    Validation:
        - latitude must be between -90 and 90
        - longitude must be between -180 and 180
        - units must be one of: 'cm', 'feet', 'inches', 'km', 'm', 'miles'
        - Inherits all validation from APObject

    https://www.w3.org/TR/activitystreams-vocabulary/#place
    """
    type: Literal["Place"] = Field(default="Place", description="Indicates that this object represents a place")
    accuracy: Optional[float] = Field(default=None, description="The accuracy of the coordinates")
    altitude: Optional[float] = Field(default=None, description="The altitude of the place")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="The latitude of the place")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="The longitude of the place")
    radius: Optional[float] = Field(default=None, description="The radius of uncertainty")
    units: Optional[str] = Field(default=None, description="The units for the radius")

    @field_validator('units')
    def validate_units(cls, v):
        valid_units = ['cm', 'feet', 'inches', 'km', 'm', 'miles']
        if v and v not in valid_units:
            raise ValueError(f"Invalid unit: {v}. Must be one of {', '.join(valid_units)}")
        return v

class APProfile(APObject):
    """
    Represents a Profile object.

    Attributes:
        type (Literal["Profile"]): Always set to "Profile".
        describes (Union[str, HttpUrl, APObject]): The object that this profile describes.

    https://www.w3.org/TR/activitystreams-vocabulary/#profile
    """
    type: Literal["Profile"] = "Profile"
    describes: Union[str, HttpUrl, APObject]

class APRelationship(APObject):
    """
    Represents a Relationship between objects.

    Attributes:
        type (Literal["Relationship"]): Always set to "Relationship".
        subject (Union[str, HttpUrl, APObject]): The subject of the relationship.
        object (Union[str, HttpUrl, APObject]): The object of the relationship.
        relationship (str): The type of relationship.

    https://www.w3.org/TR/activitystreams-vocabulary/#relationship
    """
    type: Literal["Relationship"] = "Relationship"
    subject: Union[str, HttpUrl, APObject]
    object: Union[str, HttpUrl, APObject]
    relationship: str

class APTombstone(APObject):
    """
    Represents a Tombstone (deleted object).

    Attributes:
        type (Literal["Tombstone"]): Always set to "Tombstone".
        former_type: str
        deleted: datetime

    https://www.w3.org/TR/activitystreams-vocabulary/#tombstone
    """
    type: Literal["Tombstone"] = "Tombstone"
    former_type: str
    deleted: datetime

class APArticle(APObject):
    """
    Represents an Article.

    Attributes:
        type (Literal["Article"]): Always set to "Article".

    https://www.w3.org/TR/activitystreams-vocabulary/#article
    """
    type: Literal["Article"] = "Article"

class APAudio(APObject):
    """
    Represents an Audio object.

    Attributes:
        type (Literal["Audio"]): Always set to "Audio".
        duration (Optional[str]): The duration of the audio.

    https://www.w3.org/TR/activitystreams-vocabulary/#audio
    """
    type: Literal["Audio"] = "Audio"
    duration: Optional[str] = None

class APDocument(APObject):
    """
    Represents a Document.

    Attributes:
        type (Literal["Document"]): Always set to "Document".

    https://www.w3.org/TR/activitystreams-vocabulary/#document
    """
    type: Literal["Document"] = "Document"

class APImage(APObject):
    """
    Represents an Image.

    Attributes:
        type (Literal["Image"]): Always set to "Image".
        width (Optional[int]): The width of the image.
        height (Optional[int]): The height of the image.

    https://www.w3.org/TR/activitystreams-vocabulary/#image
    """
    type: Literal["Image"] = "Image"
    width: Optional[int] = Field(None, gt=0, description="The width of the image")
    height: Optional[int] = Field(None, gt=0, description="The height of the image")

class APNote(APObject):
    """
    Represents a Note.

    Attributes:
        type (Literal["Note"]): Always set to "Note".

    https://www.w3.org/TR/activitystreams-vocabulary/#note
    """
    type: Literal["Note"] = "Note"

class APPage(APObject):
    """
    Represents a Page.

    Attributes:
        type (Literal["Page"]): Always set to "Page".

    https://www.w3.org/TR/activitystreams-vocabulary/#page
    """
    type: Literal["Page"] = "Page"

class APVideo(APObject):
    """
    Represents a Video object.

    Attributes:
        type (Literal["Video"]): Always set to "Video".
        duration (Optional[str]): The duration of the video.
        media_type (Optional[str]): The media type of the video.

    https://www.w3.org/TR/activitystreams-vocabulary/#video
    """
    type: Literal["Video"] = "Video"
    duration: Optional[str] = None
