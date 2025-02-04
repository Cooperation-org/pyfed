"""
activities.py
This module defines the Activity types for ActivityPub.
These activities are based on the ActivityStreams vocabulary.

For more information, see:
https://www.w3.org/TR/activitystreams-vocabulary/#activity-types
"""

from pydantic import Field, HttpUrl
from typing import Optional, Union, Literal, Dict, Any
from pyfed.models.objects import APObject

class APActivity(APObject):
    """
    Base class for all ActivityPub activities.
    
    An Activity is a subtype of Object that describes some form of action.

    Properties:
        actor (Union[str, HttpUrl, APObject]): The actor performing the activity.
        object (Optional[Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.
        target (Optional[Union[str, HttpUrl, APObject]]): The target of the activity.
        result (Optional[Union[str, HttpUrl, APObject, Dict[str, Any]]]): The result of the activity.
        origin (Optional[Union[str, HttpUrl, APObject]]): The origin of the activity.
        instrument (Optional[Union[str, HttpUrl, APObject]]): The instrument used to perform the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#activity
    Usage: https://www.w3.org/TR/activitypub/#activities
    """
    actor: Union[str, HttpUrl, APObject] = Field(..., description="The actor performing the activity")
    object: Optional[Union[str, HttpUrl, APObject, Dict[str, Any]]] = Field(
        default=None,
        description="The object of the activity"
    )
    target: Optional[Union[str, HttpUrl, APObject]] = Field(default=None, description="The target of the activity")
    result: Optional[Union[str, HttpUrl, APObject, Dict[str, Any]]] = Field(
        default=None,
        description="The result of the activity"
    )
    origin: Optional[Union[str, HttpUrl, APObject]] = Field(default=None, description="The origin of the activity")
    instrument: Optional[Union[str, HttpUrl, APObject]] = Field(default=None, description="The instrument used")

class APIntransitiveActivity(APActivity):
    """
    Represents an IntransitiveActivity in ActivityPub.
    
    An IntransitiveActivity is an Activity that does not have an object.

    Properties:
        type (Literal["IntransitiveActivity"]): Always set to "IntransitiveActivity".
        object (None): Always set to None for IntransitiveActivity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#intransitiveactivity
    """
    type: Literal["IntransitiveActivity"] = Field(default="IntransitiveActivity")
    object: None = None

class APCreate(APActivity):
    """
    Represents a Create activity in ActivityPub.

    Indicates that the actor has created the object.

    Attributes:
        type (Literal["Create"]): Always set to "Create".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#create
    """
    type: Literal["Create"] = Field(default="Create", description="Indicates that this object represents a create activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being created"
    )

class APUpdate(APActivity):
    """
    Represents an Update activity in ActivityPub.

    Indicates that the actor has updated the object.

    Attributes:
        type (Literal["Update"]): Always set to "Update".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#update
    """
    type: Literal["Update"] = Field(default="Update", description="Indicates that this object represents an update activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being updated"
    )

class APDelete(APActivity):
    """
    Represents a Delete activity in ActivityPub.

    Indicates that the actor has deleted the object.

    Attributes:
        type (Literal["Delete"]): Always set to "Delete".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#delete
    """
    type: Literal["Delete"] = Field(default="Delete", description="Indicates that this object represents a delete activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being deleted"
    )

class APFollow(APActivity):
    """
    Represents a Follow activity in ActivityPub.

    Indicates that the actor is "following" the object.

    Attributes:
        type (Literal["Follow"]): Always set to "Follow".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#follow
    """
    type: Literal["Follow"] = Field(default="Follow", description="Indicates that this object represents a follow activity")
    object: Union[str, HttpUrl, APObject] = Field(
        ...,  
        description="The object being followed"
    )

class APUndo(APActivity):
    """
    Represents an Undo activity in ActivityPub.

    Indicates that the actor is undoing the object activity.

    Attributes:
        type (Literal["Undo"]): Always set to "Undo".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#undo
    """
    type: Literal["Undo"] = Field(default="Undo", description="Indicates that this object represents an undo activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The activity being undone"
    )

class APLike(APActivity):
    """
    Represents a Like activity in ActivityPub.

    Indicates that the actor likes the object.

    Attributes:
        type (Literal["Like"]): Always set to "Like".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#like
    """
    type: Literal["Like"] = Field(default="Like", description="Indicates that this object represents a like activity")
    object: Union[str, HttpUrl, APObject] = Field(
        ...,  
        description="The object being liked"
    )

class APAnnounce(APActivity):
    """
    Represents an Announce activity in ActivityPub.

    Indicates that the actor is calling the target's attention to the object.

    Attributes:
        type (Literal["Announce"]): Always set to "Announce".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#announce
    """
    type: Literal["Announce"] = Field(default="Announce", description="Indicates that this object represents an announce activity")
    object: Union[str, HttpUrl, APObject] = Field(
        ...,  
        description="The object being announced"
    )

class APAccept(APActivity):
    """
    Represents an Accept activity in ActivityPub.

    Indicates that the actor accepts the object.

    Attributes:
        type (Literal["Accept"]): Always set to "Accept".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#accept
    """
    type: Literal["Accept"] = Field(default="Accept", description="Indicates that this object represents an accept activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being accepted"
    )

class APRemove(APActivity):
    """
    Represents a Remove activity in ActivityPub.

    Indicates that the actor is removing the object.

    Attributes:
        type (Literal["Remove"]): Always set to "Remove".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#remove
    """
    type: Literal["Remove"] = Field(default="Remove", description="Indicates that this object represents a remove activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being removed"
    )

class APBlock(APActivity):
    """
    Represents a Block activity in ActivityPub.

    Indicates that the actor is blocking the object.

    Attributes:
        type (Literal["Block"]): Always set to "Block".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#block
    """
    type: Literal["Block"] = Field(default="Block", description="Indicates that this object represents a block activity")
    object: Union[str, HttpUrl, APObject] = Field(
        ...,  
        description="The object being blocked"
    )

class APReject(APActivity):
    """
    Represents a Reject activity in ActivityPub.

    Indicates that the actor rejects the object.
    This is typically used to reject incoming activities such as Follow requests.

    Attributes:
        type (Literal["Reject"]): Always set to "Reject".
        object ([Union[str, HttpUrl, APObject, Dict[str, Any]]]): The object of the activity.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#reject
    """
    type: Literal["Reject"] = Field(default="Reject", description="Indicates that this object represents a reject activity")
    object: Union[str, HttpUrl, APObject, Dict[str, Any]] = Field(
        ...,  
        description="The object being rejected"
    )
