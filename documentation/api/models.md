# PyFed Models API Reference

## Overview
The models module provides Pydantic-based data models for ActivityPub objects, actors, activities, and collections. These models ensure type safety and validation while maintaining compliance with the ActivityPub protocol.

## Core Concepts

### Model Hierarchy
1. `ActivityPubBase`: Base class for all ActivityPub models
2. [APObject](cci:2://file:///Users/kene/Desktop/funkwhale-pyfed/main-lib/lastest-lib/pres_mode/pyfed/src/pyfed/models/objects.py:15:0-113:27): Base class for all ActivityPub objects
3. [APActor](cci:2://file:///Users/kene/Desktop/funkwhale-pyfed/main-lib/lastest-lib/pres_mode/pyfed/src/pyfed/models/actors.py:28:0-63:54): Base class for all ActivityPub actors
4. [APActivity](cci:2://file:///Users/kene/Desktop/funkwhale-pyfed/main-lib/lastest-lib/pres_mode/pyfed/src/pyfed/models/activities.py:13:0-41:112): Base class for all ActivityPub activities
5. [APCollection](cci:2://file:///Users/kene/Desktop/funkwhale-pyfed/main-lib/lastest-lib/pres_mode/pyfed/src/pyfed/models/collections.py:17:0-43:133): Base class for ActivityPub collections

### Common Features
- Type validation via Pydantic
- URL validation for endpoints
- JSON-LD context handling
- Federation-ready serialization

## Base Models

### ActivityPubBase
The foundation class for all ActivityPub models.

```python
class ActivityPubBase(BaseModel):
    """Base model for all ActivityPub objects."""
    
    context: Union[str, List[str]] = Field(
        default="https://www.w3.org/ns/activitystreams",
        alias="@context"
    )
    id: Optional[HttpUrl] = None
    type: str

APObject
Base class for all ActivityPub objects.
class APObject(ActivityPubBase):
    """Base class for ActivityPub objects."""
    
    attachment: Optional[List[Union[APObject, APLink]]] = None
    attributedTo: Optional[Union[str, List[str]]] = None
    audience: Optional[List[str]] = None
    content: Optional[str] = None
    name: Optional[str] = None
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    tag: Optional[List[Dict[str, Any]]] = None
    
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

Actor Models
APActor
Base class for all ActivityPub actors.
class APActor(APObject):
    """Base class for ActivityPub actors."""
    
    inbox: HttpUrl
    outbox: HttpUrl
    following: Optional[HttpUrl] = None
    followers: Optional[HttpUrl] = None
    liked: Optional[HttpUrl] = None
    
    @field_validator('inbox', 'outbox', 'following', 'followers', 'liked')
    @classmethod
    def validate_urls(cls, v):
        """Validate actor endpoints are valid URLs."""
        try:
            return HttpUrl(v)
        except ValueError:
            raise InvalidURLError(f"Invalid URL: {v}")

Actor Types
APPerson
Represents a person in the federation.
class APPerson(APActor):
    """Model for Person actors."""
    type: Literal["Person"]

APGroup
Represents a group in the federation.
class APGroup(APActor):
    """Model for Group actors."""
    type: Literal["Group"]

APService
Represents a service in the federation.
class APService(APActor):
    """Model for Service actors."""
    type: Literal["Service"]

APOrganization
Represents an organization in the federation.
class APOrganization(APActor):
    """Model for Organization actors."""
    type: Literal["Organization"]

APApplication
Represents an application in the federation.
class APApplication(APActor):
    """Model for Application actors."""
    type: Literal["Application"]

Object Types
Content Objects
APNote
Represents a note or status update.
class APNote(APObject):
    """Model for Note objects."""
    type: Literal["Note"]
    content: str

APArticle
Represents a full article or blog post.
class APArticle(APObject):
    """Model for Article objects."""
    type: Literal["Article"]
    content: str
    summary: Optional[str] = None

Media Objects
APImage
Represents an image object.
class APImage(APObject):
    """Model for Image objects."""
    type: Literal["Image"]
    url: Union[str, List[str]]

APVideo
Represents a video object.
class APVideo(APObject):
    """Model for Video objects."""
    type: Literal["Video"]
    url: Union[str, List[str]]

Collection Models
APCollection
Base class for collections.
class APCollection(APObject):
    """Base class for ActivityPub collections."""
    
    totalItems: Optional[int] = None
    items: Optional[List[Union[APObject, Dict[str, Any]]]] = None
    current: Optional[Union[str, "APCollectionPage"]] = None
    first: Optional[Union[str, "APCollectionPage"]] = None
    last: Optional[Union[str, "APCollectionPage"]] = None

APOrderedCollection
Collection with ordered items.
class APOrderedCollection(APCollection):
    """Model for ordered collections."""
    
    type: Literal["OrderedCollection"]
    orderedItems: Optional[List[Union[APObject, Dict[str, Any]]]] = None

Activity Models
APActivity
Base class for all activities.
class APActivity(APObject):
    """Base class for ActivityPub activities."""
    
    actor: Union[str, APActor]
    object: Optional[Union[str, APObject, Dict[str, Any]]] = None

Common Activities
APCreate
Represents object creation.class APCreate(APActivity):
    """Model for Create activities."""
    type: Literal["Create"]
    object: Union[str, APObject, Dict[str, Any]]

APUpdate
Represents object updates.
class APUpdate(APActivity):
    """Model for Update activities."""
    type: Literal["Update"]
    object: Union[str, APObject, Dict[str, Any]]

APDelete
Represents object deletion.
class APDelete(APActivity):
    """Model for Delete activities."""
    type: Literal["Delete"]
    object: Union[str, APObject, Dict[str, Any]]

Usage Examples
Creating an Actor
person = APPerson(
    id="https://example.com/users/alice",
    name="Alice",
    inbox="https://example.com/users/alice/inbox",
    outbox="https://example.com/users/alice/outbox",
    following="https://example.com/users/alice/following",
    followers="https://example.com/users/alice/followers"
)

Creating a Note
note = APNote(
    id="https://example.com/notes/1",
    content="Hello, Federation!",
    attributedTo="https://example.com/users/alice",
    to=["https://www.w3.org/ns/activitystreams#Public"],
    cc=["https://example.com/users/alice/followers"]
)

Creating an Activity
create = APCreate(
    id="https://example.com/activities/1",
    actor="https://example.com/users/alice",
    object=note,
    to=note.to,
    cc=note.cc
)

Error Handling
Common Exceptions
class InvalidURLError(ValueError):
    """Raised when a URL is invalid."""
    pass

class ValidationError(Exception):
    """Raised when model validation fails."""
    pass

Validation Best Practices
Always validate URLs using the provided validators
Use type hints and Pydantic validators
Handle validation errors appropriately
Log validation failures for debugging

Configuration
Model Configuration
class Config:
    """Pydantic model configuration."""
    
    allow_population_by_field_name = True
    json_encoders = {
        datetime: lambda v: v.isoformat() + "Z",
        HttpUrl: str
    }

##### See Also
- [Security Guide](security.md)
- [ActivityPub Specification](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-activitypub)