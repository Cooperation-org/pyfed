"""
Collection handling implementation.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio

from ..utils.exceptions import CollectionError
from ..utils.logging import get_logger
from ..storage.base import StorageBackend

logger = get_logger(__name__)

class CollectionHandler:
    """Handle ActivityPub collections."""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def create_collection(self,
                              collection_type: str,
                              owner: str,
                              items: Optional[List[str]] = None) -> str:
        """
        Create a new collection.
        
        Args:
            collection_type: Collection type (OrderedCollection or Collection)
            owner: Collection owner
            items: Initial collection items
            
        Returns:
            Collection ID
        """
        try:
            collection = {
                "type": collection_type,
                "attributedTo": owner,
                "totalItems": len(items) if items else 0,
                "items": items or [],
                "published": datetime.utcnow().isoformat()
            }
            
            collection_id = await self.storage.create_object(collection)
            return collection_id
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise CollectionError(f"Failed to create collection: {e}")

    async def add_to_collection(self,
                              collection_id: str,
                              items: Union[str, List[str]]) -> None:
        """
        Add items to collection.
        
        Args:
            collection_id: Collection ID
            items: Item(s) to add
        """
        try:
            collection = await self.storage.get_object(collection_id)
            if not collection:
                raise CollectionError(f"Collection not found: {collection_id}")
            
            if isinstance(items, str):
                items = [items]
            
            # Add items
            current_items = collection.get('items', [])
            new_items = list(set(current_items + items))
            
            # Update collection
            collection['items'] = new_items
            collection['totalItems'] = len(new_items)
            
            await self.storage.update_object(collection_id, collection)
            
        except Exception as e:
            logger.error(f"Failed to add to collection: {e}")
            raise CollectionError(f"Failed to add to collection: {e}")

    async def remove_from_collection(self,
                                   collection_id: str,
                                   items: Union[str, List[str]]) -> None:
        """
        Remove items from collection.
        
        Args:
            collection_id: Collection ID
            items: Item(s) to remove
        """
        try:
            collection = await self.storage.get_object(collection_id)
            if not collection:
                raise CollectionError(f"Collection not found: {collection_id}")
            
            if isinstance(items, str):
                items = [items]
            
            # Remove items
            current_items = collection.get('items', [])
            new_items = [i for i in current_items if i not in items]
            
            # Update collection
            collection['items'] = new_items
            collection['totalItems'] = len(new_items)
            
            await self.storage.update_object(collection_id, collection)
            
        except Exception as e:
            logger.error(f"Failed to remove from collection: {e}")
            raise CollectionError(f"Failed to remove from collection: {e}")

    async def get_collection_page(self,
                                collection_id: str,
                                page: int = 1,
                                per_page: int = 20) -> Dict[str, Any]:
        """
        Get collection page.
        
        Args:
            collection_id: Collection ID
            page: Page number
            per_page: Items per page
            
        Returns:
            Collection page
        """
        try:
            collection = await self.storage.get_object(collection_id)
            if not collection:
                raise CollectionError(f"Collection not found: {collection_id}")
            
            items = collection.get('items', [])
            total = len(items)
            
            # Calculate pagination
            start = (page - 1) * per_page
            end = start + per_page
            page_items = items[start:end]
            
            return {
                "type": "OrderedCollectionPage",
                "partOf": collection_id,
                "orderedItems": page_items,
                "totalItems": total,
                "current": f"{collection_id}?page={page}",
                "first": f"{collection_id}?page=1",
                "last": f"{collection_id}?page={-(-total // per_page)}",
                "next": f"{collection_id}?page={page + 1}" if end < total else None,
                "prev": f"{collection_id}?page={page - 1}" if page > 1 else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection page: {e}")
            raise CollectionError(f"Failed to get collection page: {e}")

    async def merge_collections(self,
                              target_id: str,
                              source_id: str) -> None:
        """
        Merge two collections.
        
        Args:
            target_id: Target collection ID
            source_id: Source collection ID
        """
        try:
            target = await self.storage.get_object(target_id)
            source = await self.storage.get_object(source_id)
            
            if not target or not source:
                raise CollectionError("Collection not found")
            
            # Merge items
            target_items = target.get('items', [])
            source_items = source.get('items', [])
            merged_items = list(set(target_items + source_items))
            
            # Update target
            target['items'] = merged_items
            target['totalItems'] = len(merged_items)
            
            await self.storage.update_object(target_id, target)
            
        except Exception as e:
            logger.error(f"Failed to merge collections: {e}")
            raise CollectionError(f"Failed to merge collections: {e}") 