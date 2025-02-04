"""
test_collections.py
This module contains tests for the Collection types in ActivityPub.
"""
import pytest
from pydantic import ValidationError
from pyfed.models import (
    APCollection, APOrderedCollection,
    APCollectionPage, APOrderedCollectionPage
)

def test_valid_collection():
    """Test creating a valid Collection."""
    collection = APCollection(
        id="https://example.com/collection/123",
        total_items=10,
        items=["https://example.com/item/1", "https://example.com/item/2"]
    )
    assert collection.type == "Collection"
    assert collection.total_items == 10
    assert len(collection.items) == 2

def test_collection_with_optional_fields():
    """Test creating a Collection with all optional fields."""
    collection = APCollection(
        id="https://example.com/collection/123",
        total_items=2,
        current="https://example.com/collection/123/current",
        first="https://example.com/collection/123/first",
        last="https://example.com/collection/123/last",
        items=["https://example.com/item/1", "https://example.com/item/2"]
    )
    assert str(collection.current) == "https://example.com/collection/123/current"
    assert str(collection.first) == "https://example.com/collection/123/first"
    assert str(collection.last) == "https://example.com/collection/123/last"

def test_invalid_collection_negative_total():
    """Test that Collection creation fails with negative total_items."""
    with pytest.raises(ValidationError):
        APCollection(
            id="https://example.com/collection/123",
            type="Collection",
            total_items=-1
        )

def test_valid_ordered_collection():
    """Test creating a valid OrderedCollection."""
    collection = APOrderedCollection(
        id="https://example.com/collection/123",
        total_items=2,
        ordered_items=["https://example.com/item/1", "https://example.com/item/2"]
    )
    assert collection.type == "OrderedCollection"
    assert len(collection.ordered_items) == 2

def test_valid_collection_page():
    """Test creating a valid CollectionPage."""
    page = APCollectionPage(
        id="https://example.com/collection/123/page/1",
        part_of="https://example.com/collection/123",
        items=["https://example.com/item/1"]
    )
    assert page.type == "CollectionPage"
    assert str(page.part_of) == "https://example.com/collection/123"

def test_collection_page_with_navigation():
    """Test creating a CollectionPage with navigation links."""
    page = APCollectionPage(
        id="https://example.com/collection/123/page/2",
        part_of="https://example.com/collection/123",
        items=["https://example.com/item/2"],
        next="https://example.com/collection/123/page/3",
        prev="https://example.com/collection/123/page/1"
    )
    assert str(page.next) == "https://example.com/collection/123/page/3"
    assert str(page.prev) == "https://example.com/collection/123/page/1"

def test_valid_ordered_collection_page():
    """Test creating a valid OrderedCollectionPage."""
    page = APOrderedCollectionPage(
        id="https://example.com/collection/123/page/1",
        part_of="https://example.com/collection/123",
        ordered_items=["https://example.com/item/1"],
        start_index=0
    )
    assert page.type == "OrderedCollectionPage"
    assert page.start_index == 0

def test_invalid_ordered_page_negative_index():
    """Test that OrderedCollectionPage creation fails with negative start_index."""
    with pytest.raises(ValidationError):
        APOrderedCollectionPage(
            id="https://example.com/collection/123/page/1",
            start_index=-1
        )

def test_collection_with_object_items():
    """Test creating a Collection with APObject items."""
    collection = APCollection(
        id="https://example.com/collection/123",
        items=[{
            "id": "https://example.com/item/1",
            "type": "Note",
            "content": "Test note"
        }]
    )
    assert len(collection.items) == 1
    assert collection.items[0]["type"] == "Note"

def test_ordered_collection_empty():
    """Test creating an empty OrderedCollection."""
    collection = APOrderedCollection(
        id="https://example.com/collection/123",
        total_items=0
    )
    assert collection.total_items == 0
    assert collection.ordered_items is None
