"""
pyfed package initialization.
"""
# from .plugins import plugin_manager  # Update the import path

# Export all models
from .models import (
    APObject, APEvent, APPlace, APProfile, APRelationship, APTombstone,
    APArticle, APAudio, APDocument, APImage, APNote, APPage, APVideo,
    APActor, APPerson, APGroup, APOrganization, APApplication, APService,
    APLink, APMention,
    APCollection, APOrderedCollection, APCollectionPage, APOrderedCollectionPage,
    APCreate, APUpdate, APDelete, APFollow, APUndo, APLike, APAnnounce
)

# Export serializers
from .serializers.json_serializer import ActivityPubSerializer

__all__ = [
    'APObject', 'APEvent', 'APPlace', 'APProfile', 'APRelationship', 'APTombstone',
    'APArticle', 'APAudio', 'APDocument', 'APImage', 'APNote', 'APPage', 'APVideo',
    'APActor', 'APPerson', 'APGroup', 'APOrganization', 'APApplication', 'APService',
    'APLink', 'APMention',
    'APCollection', 'APOrderedCollection', 'APCollectionPage', 'APOrderedCollectionPage',
    'APCreate', 'APUpdate', 'APDelete', 'APFollow', 'APUndo', 'APLike', 'APAnnounce',
    'ActivityPubSerializer'
]
