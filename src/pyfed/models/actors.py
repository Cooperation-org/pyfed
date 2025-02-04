"""
actors.py
This module defines the Actor types for ActivityPub.
These actors are based on the ActivityStreams vocabulary and ActivityPub protocol.

For more information on Actors in ActivityPub, see:
https://www.w3.org/TR/activitypub/#actors
"""

from __future__ import annotations
from pydantic import Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any, TypedDict, Literal
from datetime import datetime
from ..utils.exceptions import InvalidURLError
from ..utils.logging import get_logger
from ..cache import object_cache

from .objects import APObject

logger = get_logger(__name__)

class ActivityDict(TypedDict):
    actor: str
    object: Dict[str, Any]
    published: str
    type: str
    context: str

class APActor(APObject):
    """
    Base Actor type as defined in ActivityPub.

    Properties:
        type (Literal["Person"]): Always set to "Person".
        inbox (HttpUrl): The actor's inbox URL.
        outbox (HttpUrl): The actor's outbox URL.
        following (Optional[HttpUrl]): The actor's following collection URL.
        followers (Optional[HttpUrl]): The actor's followers collection URL.
        liked (Optional[HttpUrl]): The actor's liked collection URL.
        streams (Optional[List[HttpUrl]]): Additional streams.
        preferred_username (Optional[str]): The actor's preferred username.
        endpoints (Optional[Dict[str, HttpUrl]]): Additional endpoints.
        public_key (Optional[Dict[str, str]]): Public key information.

    Specification: https://www.w3.org/TR/activitypub/#actor-objects
    Usage: https://www.w3.org/TR/activitypub/#actor-objects
    """
    inbox: HttpUrl = Field(..., description="Primary inbox URL")
    outbox: HttpUrl = Field(..., description="Primary outbox URL")
    following: Optional[HttpUrl] = Field(default=None, description="Following collection")
    followers: Optional[HttpUrl] = Field(default=None, description="Followers collection")
    liked: Optional[HttpUrl] = Field(default=None, description="Liked collection")
    streams: Optional[List[HttpUrl]] = Field(default=None, description="Additional streams")
    preferred_username: Optional[str] = Field(default=None, description="Preferred username")
    endpoints: Optional[Dict[str, HttpUrl]] = Field(default=None, description="Additional endpoints")
    public_key: Optional[Dict[str, str]] = Field(default=None, description="Public key information")

    @field_validator('inbox', 'outbox', 'following', 'followers', 'liked')
    @classmethod
    def validate_urls(cls, v):
        try:
            return HttpUrl(v)
        except ValueError:
            raise InvalidURLError(f"Invalid URL: {v}")

class APPerson(APActor):
    """
    Represents a Person actor in ActivityPub.

    A Person is an individual user account.

    Properties:
        type (Literal["Person"]): Always set to "Person".

    Inherits all other properties from APActor.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-person
    """
    type: Literal["Person"] = Field(default="Person", description="Indicates that this object represents a person")

class APGroup(APActor):
    """
    Represents a Group actor in ActivityPub.

    A Group represents a formal or informal collective of Actors.

    Attributes:
        type (str): Always set to "Group".

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-group
    """
    type: Literal["Group"] = Field(default="Group", description="Indicates that this object represents a group")

class APOrganization(APActor):
    """
    Represents an Organization actor in ActivityPub.

    An Organization is a kind of Actor representing a formal or informal organization.

    Attributes:
        type (str): Always set to "Organization".

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-organization
    """
    type: Literal["Organization"] = Field(default="Organization", description="Indicates that this object represents an organization")

class APApplication(APActor):
    """
    Represents an Application actor in ActivityPub.

    An Application represents a software application.

    Attributes:
        type (str): Always set to "Application".

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-application
    """
    type: Literal["Application"] = Field(default="Application", description="Indicates that this object represents an application")

class APService(APActor):
    """
    Represents a Service actor in ActivityPub.

    A Service is a kind of Actor that represents a service of any kind.

    Attributes:
        type (str): Always set to "Service".

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-service
    """
    type: Literal["Service"] = Field(default="Service", description="Indicates that this object represents a service")
