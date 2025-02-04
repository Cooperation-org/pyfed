"""
test_imports.py
This module tests that all necessary modules can be imported correctly.
"""

import pytest
from pyfed.serializers.json_serializer import ActivityPubSerializer
# from pyfed.plugins import plugin_manager  # Updated import path
from pyfed.models import (
    APObject, APEvent, APPlace, APProfile, APRelationship, APTombstone,
    APArticle, APAudio, APDocument, APImage, APNote, APPage, APVideo,
    APActor, APPerson, APGroup, APOrganization, APApplication, APService,
    APLink, APMention,
    APCollection, APOrderedCollection, APCollectionPage, APOrderedCollectionPage,
    APCreate, APUpdate, APDelete, APFollow, APUndo, APLike, APAnnounce
)

def test_can_import_models():
    """Test that all models can be imported."""
    assert APObject
    assert APEvent
    assert APPlace
    assert APProfile
    assert APRelationship
    assert APTombstone
    assert APArticle
    assert APAudio
    assert APDocument
    assert APImage
    assert APNote
    assert APPage
    assert APVideo

def test_can_import_actors():
    """Test that all actor types can be imported."""
    assert APActor
    assert APPerson
    assert APGroup
    assert APOrganization
    assert APApplication
    assert APService

def test_can_import_links():
    """Test that all link types can be imported."""
    assert APLink
    assert APMention

def test_can_import_collections():
    """Test that all collection types can be imported."""
    assert APCollection
    assert APOrderedCollection
    assert APCollectionPage
    assert APOrderedCollectionPage

def test_can_import_activities():
    """Test that all activity types can be imported."""
    assert APCreate
    assert APUpdate
    assert APDelete
    assert APFollow
    assert APUndo
    assert APLike
    assert APAnnounce

def test_can_import_serializer():
    """Test that the serializer can be imported."""
    assert ActivityPubSerializer
