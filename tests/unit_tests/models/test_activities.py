"""
test_activities.py
This module contains tests for the Activity types in ActivityPub.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from pyfed.models import (
    APCreate, APUpdate, APDelete, APFollow,
    APUndo, APLike, APAnnounce
)

def test_create_activity():
    """Test creating a Create activity."""
    activity = APCreate(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object={
            "id": "https://example.com/note/123",
            "type": "Note",
            "content": "Hello, World!"
        }
    )
    assert activity.type == "Create"
    assert str(activity.actor) == "https://example.com/user/1"
    assert activity.object["type"] == "Note"

def test_update_activity():
    """Test creating an Update activity."""
    activity = APUpdate(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object={
            "id": "https://example.com/note/123",
            "type": "Note",
            "content": "Updated content"
        }
    )
    assert activity.type == "Update"
    assert activity.object["content"] == "Updated content"

def test_delete_activity():
    """Test creating a Delete activity."""
    activity = APDelete(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/note/123"
    )
    assert activity.type == "Delete"
    assert str(activity.object) == "https://example.com/note/123"

def test_follow_activity():
    """Test creating a Follow activity."""
    activity = APFollow(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/user/2"
    )
    assert activity.type == "Follow"
    assert str(activity.object) == "https://example.com/user/2"

def test_undo_activity():
    """Test creating an Undo activity."""
    activity = APUndo(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object={
            "id": "https://example.com/activity/456",
            "type": "Follow",
            "actor": "https://example.com/user/1",
            "object": "https://example.com/user/2"
        }
    )
    assert activity.type == "Undo"
    assert activity.object["type"] == "Follow"

def test_like_activity():
    """Test creating a Like activity."""
    activity = APLike(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/note/123"
    )
    assert activity.type == "Like"
    assert str(activity.object) == "https://example.com/note/123"

def test_announce_activity():
    """Test creating an Announce activity."""
    activity = APAnnounce(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/note/123"
    )
    assert activity.type == "Announce"
    assert str(activity.object) == "https://example.com/note/123"

def test_activity_with_target():
    """Test creating an activity with a target."""
    activity = APCreate(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/note/123",
        target="https://example.com/collection/1"
    )
    assert str(activity.target) == "https://example.com/collection/1"

def test_activity_with_result():
    """Test creating an activity with a result."""
    activity = APCreate(
        id="https://example.com/activity/123",
        actor="https://example.com/user/1",
        object="https://example.com/note/123",
        result={
            "id": "https://example.com/result/1",
            "type": "Note",
            "content": "Result content"
        }
    )
    assert activity.result["type"] == "Note"

def test_invalid_activity_missing_actor():
    """Test that activity creation fails when actor is missing."""
    with pytest.raises(ValidationError):
        APCreate(
            id="https://example.com/activity/123",
            object="https://example.com/note/123"
        )

def test_invalid_activity_missing_object():
    """Test that activity creation fails when object is missing for non-intransitive activities."""
    with pytest.raises(ValidationError):
        APCreate(
            id="https://example.com/activity/123",
            actor="https://example.com/user/1"
        )
