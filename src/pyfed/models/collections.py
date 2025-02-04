"""
collections.py
This module defines the Collection types for ActivityPub.
These collections are based on the ActivityStreams vocabulary and ActivityPub protocol.

For more information on Collections in ActivityStreams, see:
https://www.w3.org/TR/activitystreams-core/#collections
"""

from __future__ import annotations
from typing import Optional, List, Union, Literal, Dict, Any
from pydantic import Field, BaseModel, HttpUrl
from pyfed.models.objects import APObject
from pyfed.utils.logging import get_logger

logger = get_logger(__name__)

class APCollection(APObject):
    """
    Represents a Collection in ActivityPub.
    
    A Collection is an unordered set of Objects or Links.

    Properties:
        type (Literal["Collection"]): Always set to "Collection".
        total_items (Optional[int]): The total number of items in the collection.
        current (Optional[Union[str, HttpUrl, 'APCollectionPage']]): The current page.
        first (Optional[Union[str, HttpUrl, 'APCollectionPage']]): The first page.
        last (Optional[Union[str, HttpUrl, 'APCollectionPage']]): The last page.
        items (Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]]): The items.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#collection
    Usage: https://www.w3.org/TR/activitypub/#collections
    """
    type: Literal["Collection"] = Field(default="Collection", description="Indicates a Collection")
    total_items: Optional[int] = Field(
        default=None,
        ge=0,  # Greater than or equal to 0
        description="Total number of items"
    )
    current: Optional[Union[str, HttpUrl, 'APCollectionPage']] = Field(default=None, description="Current page")
    first: Optional[Union[str, HttpUrl, 'APCollectionPage']] = Field(default=None, description="First page")
    last: Optional[Union[str, HttpUrl, 'APCollectionPage']] = Field(default=None, description="Last page")
    items: Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]] = Field(default=None, description="Items in the collection")

class APOrderedCollection(APCollection):
    """
    Represents an OrderedCollection in ActivityPub.
    
    An OrderedCollection is a Collection where the items are strictly ordered.

    Properties:
        type (Literal["OrderedCollection"]): Always set to "OrderedCollection".
        ordered_items (Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]]): The ordered items.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#orderedcollection
    Usage: https://www.w3.org/TR/activitypub/#ordered-collections
    """
    type: Literal["OrderedCollection"] = Field(default="OrderedCollection", description="Indicates an OrderedCollection")
    ordered_items: Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]] = Field(default=None, description="The ordered items")

class APCollectionPage(APCollection):
    """
    Represents a CollectionPage in ActivityPub.
    
    A CollectionPage represents a single page of a Collection.

    Properties:
        type (Literal["CollectionPage"]): Always set to "CollectionPage".
        part_of (Optional[Union[str, HttpUrl, APCollection]]): The parent collection.
        next (Optional[Union[str, HttpUrl, 'APCollectionPage']]): The next page.
        prev (Optional[Union[str, HttpUrl, 'APCollectionPage']]): The previous page.

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#collectionpage
    Usage: https://www.w3.org/TR/activitypub/#collection-paging
    """
    type: Literal["CollectionPage"] = Field(default="CollectionPage", description="Indicates a CollectionPage")
    part_of: Optional[Union[str, HttpUrl, APCollection]] = Field(default=None, description="The parent collection")
    next: Optional[Union[str, HttpUrl, 'APCollectionPage']] = Field(default=None, description="The next page")
    prev: Optional[Union[str, HttpUrl, 'APCollectionPage']] = Field(default=None, description="The previous page")

class APOrderedCollectionPage(APCollectionPage):
    """
    Represents an OrderedCollectionPage in ActivityPub.
    
    An OrderedCollectionPage represents a single page of an OrderedCollection.

    Properties:
        type (Literal["OrderedCollectionPage"]): Always set to "OrderedCollectionPage".
        ordered_items (Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]]): The ordered items.
        start_index (Optional[int]): The index of the first item (0-based).

    Specification: https://www.w3.org/TR/activitystreams-vocabulary/#orderedcollectionpage
    Usage: https://www.w3.org/TR/activitypub/#ordered-collection-paging
    """
    type: Literal["OrderedCollectionPage"] = Field(default="OrderedCollectionPage", description="Indicates an OrderedCollectionPage")
    ordered_items: Optional[List[Union[str, HttpUrl, Dict[str, Any], APObject]]] = Field(default=None, description="The ordered items")
    start_index: Optional[int] = Field(
        default=None,
        ge=0,  # Greater than or equal to 0
        description="The index of the first item"
    )

class APFollowersCollection(APOrderedCollection):
    """Collection of followers."""
    type: Literal["OrderedCollection"] = Field(default="OrderedCollection", description="Indicates an OrderedCollection")
    name: Literal["Followers"] = Field(default="Followers")

class APFollowingCollection(APOrderedCollection):
    """Collection of following."""
    type: Literal["OrderedCollection"] = Field(default="OrderedCollection", description="Indicates an OrderedCollection")
    name: Literal["Following"] = Field(default="Following")

class APLikedCollection(APOrderedCollection):
    """Collection of liked objects."""
    type: Literal["OrderedCollection"] = Field(default="OrderedCollection", description="Indicates an OrderedCollection")
    name: Literal["Liked"] = Field(default="Liked")

class APSharedCollection(APOrderedCollection):
    """Collection of shared objects."""
    type: Literal["OrderedCollection"] = Field(default="OrderedCollection", description="Indicates an OrderedCollection")
    name: Literal["Shared"] = Field(default="Shared")

async def fetch_collection(url: str) -> Union[APCollection, APOrderedCollection]:
    """
    Fetch a collection from a given URL.

    Args:
        url (str): The URL of the collection to fetch.

    Returns:
        Union[APCollection, APOrderedCollection]: The fetched collection.

    Note: This is a placeholder implementation. In a real-world scenario,
    this would involve making an HTTP request to the given URL and
    parsing the response into the appropriate collection type.
    """
    logger.info(f"Fetching collection from: {url}")
    # Placeholder implementation
    # print(f"Fetching collection from: {url}")
    return APCollection(id=url, type="Collection", totalItems=0)

async def paginate_collection(collection: Union[APCollection, APOrderedCollection], page_size: int = 10) -> List[Union[APCollectionPage, APOrderedCollectionPage]]:
    """
    Paginate a collection into smaller pages.

    Args:
        collection (Union[APCollection, APOrderedCollection]): The collection to paginate.
        page_size (int): The number of items per page.

    Returns:
        List[Union[APCollectionPage, APOrderedCollectionPage]]: A list of collection pages.

    Note: This is a placeholder implementation. In a real-world scenario,
    this would involve creating actual page objects and properly linking them.
    """
    logger.info(f"Paginating collection: {collection.id}")
    # Placeholder implementation
    # print(f"Paginating collection: {collection.id}")
    return []
