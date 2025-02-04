"""
Tests for ActivityPub serialization.
"""

import pytest
from datetime import datetime, timezone
import json

from pyfed.models import (
    APObject, APNote, APPerson, APCollection,
    APCreate, APPlace, APEvent
)
from pyfed.serializers.json_serializer import ActivityPubSerializer

def test_serialize_ap_object():
    """Test basic object serialization."""
    obj = APObject(
        id="https://example.com/object/123",
        type="Object",
        name="Test Object",
        content="This is a test object."
    )
    serialized = obj.serialize()
    
    # Verify serialization
    assert serialized["@context"] == ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1']
    assert serialized["id"] == "https://example.com/object/123"
    assert serialized["type"] == "Object"
    assert serialized["name"] == "Test Object"
    assert serialized["content"] == "This is a test object."

def test_serialize_with_datetime():
    """Test serialization of objects with datetime fields."""
    now = datetime.now(timezone.utc)
    obj = APObject(
        id="https://example.com/object/123",
        type="Object",
        published=now,
        updated=now
    )
    serialized = obj.serialize()
    
    # Verify datetime serialization
    assert serialized["published"] == now.isoformat()
    assert serialized["updated"] == now.isoformat()

def test_serialize_nested_objects():
    """Test serialization of objects with nested objects."""
    author = APPerson(
        id="https://example.com/users/alice",
        name="Alice",
        inbox="https://example.com/users/alice/inbox",
        outbox="https://example.com/users/alice/outbox"
    )
    note = APNote(
        id="https://example.com/notes/123",
        content="Hello, World!",
        attributed_to=author
    )
    serialized = note.serialize()
    
    # Verify nested object serialization
    assert serialized["attributedTo"]["id"] == "https://example.com/users/alice"
    assert serialized["attributedTo"]["type"] == "Person"
    assert serialized["attributedTo"]["name"] == "Alice"

def test_serialize_collection():
    """Test serialization of collections."""
    items = [
        APNote(
            id=f"https://example.com/notes/{i}",
            content=f"Note {i}"
        ).serialize() for i in range(3)
    ]
    collection = APCollection(
        id="https://example.com/collection/1",
        total_items=len(items),
        items=items
    )
    serialized = collection.serialize()
    
    # Verify collection serialization
    assert serialized["type"] == "Collection"
    assert serialized["totalItems"] == 3
    assert len(serialized["items"]) == 3
    assert all(item["type"] == "Note" for item in serialized["items"])

def test_serialize_activity():
    """Test serialization of activities."""
    note = APNote(
        id="https://example.com/notes/123",
        content="Hello, World!"
    ).serialize()
    create = APCreate(
        id="https://example.com/activities/1",
        actor="https://example.com/users/alice",
        object=note
    )
    serialized = create.serialize()
    
    # Verify activity serialization
    assert serialized["type"] == "Create"
    assert serialized["actor"] == "https://example.com/users/alice"
    assert serialized["object"]["type"] == "Note"
    assert serialized["object"]["content"] == "Hello, World!"

def test_deserialize_ap_object():
    """Test basic object deserialization."""
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Object",
        "id": "https://example.com/object/123",
        "name": "Test Object",
        "content": "This is a test object."
    }
    obj = ActivityPubSerializer.deserialize(data, APObject)
    
    # Verify deserialization
    assert str(obj.id) == "https://example.com/object/123"
    assert obj.type == "Object"
    assert obj.name == "Test Object"
    assert obj.content == "This is a test object."

def test_deserialize_from_json_string():
    """Test deserialization from JSON string."""
    json_str = json.dumps({
        "type": "Object",
        "id": "https://example.com/object/123",
        "name": "Test Object"
    })
    obj = ActivityPubSerializer.deserialize(json_str, APObject)
    
    # Verify deserialization from string
    assert str(obj.id) == "https://example.com/object/123"
    assert obj.type == "Object"
    assert obj.name == "Test Object"

def test_deserialize_invalid_json():
    """Test deserialization of invalid JSON."""
    with pytest.raises(ValueError):
        ActivityPubSerializer.deserialize("invalid json", APObject)

def test_deserialize_missing_required_fields():
    """Test deserialization with missing required fields."""
    data = {"type": "Object", "name": "Test"}  # Missing required 'id'
    with pytest.raises(Exception):  # Pydantic will raise validation error
        ActivityPubSerializer.deserialize(data, APObject)

def test_serialize_deserialize_complex_object():
    """Test round-trip serialization and deserialization."""
    original = APNote(
        id="https://example.com/notes/123",
        content="Test content",
        to=["https://example.com/users/bob"],
        cc=["https://www.w3.org/ns/activitystreams#Public"]
    )
    serialized = original.serialize()
    deserialized = ActivityPubSerializer.deserialize(serialized, APNote)
    
    # Verify round-trip
    assert str(deserialized.id) == str(original.id)
    assert deserialized.type == original.type
    assert deserialized.content == original.content
    assert deserialized.to == original.to
    assert deserialized.cc == original.cc

def test_deserialize_with_extra_fields():
    """Test deserialization with extra fields in JSON."""
    data = {
        "type": "Object",
        "id": "https://example.com/object/123",
        "name": "Test Object",
        "extra_field": "Should be ignored"
    }
    obj = ActivityPubSerializer.deserialize(data, APObject)
    
    # Verify extra fields are handled
    assert str(obj.id) == "https://example.com/object/123"
    assert obj.type == "Object"
    assert obj.name == "Test Object"
