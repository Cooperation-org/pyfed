"""
test_interactions.py
This module contains tests for the interactions between ActivityPub models.
"""
import pytest
from datetime import datetime, timedelta
from pyfed.models import (
    APEvent, APPlace, APPerson, APNote, APObject, APImage,
    APCollection, APOrderedCollection, APLink, APMention,
    APCreate, APLike, APFollow, APAnnounce, APUpdate, APDelete,
    APUndo, APDocument, APGroup, APOrganization, APOrderedCollectionPage,
    APRelationship
)

def test_event_with_place_and_attendees():
    """Test creating an event with a location and attendees."""
    place = APPlace(
        id="https://example.com/place/123",
        name="Event Venue",
        latitude=52.5200,
        longitude=13.4050
    )
    attendee1 = APPerson(
        id="https://example.com/person/1",
        name="John Doe",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    attendee2 = APPerson(
        id="https://example.com/person/2",
        name="Jane Doe",
        inbox="https://example.com/person/2/inbox",
        outbox="https://example.com/person/2/outbox"
    )
    event = APEvent(
        id="https://example.com/event/123",
        name="Test Event",
        location=place,
        to=[str(attendee1.id), str(attendee2.id)]
    )
    assert str(event.location.id) == "https://example.com/place/123"
    assert event.location.name == "Event Venue"
    assert len(event.to) == 2

def test_note_with_mentions_and_attachments():
    """Test creating a note with mentions and attachments."""
    mentioned_person = APPerson(
        id="https://example.com/person/1",
        name="John Doe",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    image = APImage(
        id="https://example.com/image/1",
        type="Image",
        url="https://example.com/image.jpg",
        width=800,
        height=600
    )
    note = APNote(
        id="https://example.com/note/123",
        content="Hello @John! Check out this image.",
        tag=[{"type": "Mention", "href": str(mentioned_person.id)}],
        attachment=[image]
    )
    assert len(note.tag) == 1
    assert len(note.attachment) == 1
    assert isinstance(note.attachment[0], APImage)

def test_collection_with_pagination():
    """Test creating a collection with pagination."""
    items = [
        APNote(
            id=f"https://example.com/note/{i}",
            content=f"Note {i}"
        ) for i in range(1, 6)
    ]
    collection = APCollection(
        id="https://example.com/collection/123",
        total_items=len(items),
        items=items,
        first="https://example.com/collection/123?page=1",
        last="https://example.com/collection/123?page=1"
    )
    assert collection.total_items == 5
    assert len(collection.items) == 5
    assert str(collection.first).endswith("page=1")

def test_create_activity_with_note():
    """Test creating a Create activity with a note."""
    author = APPerson(
        id="https://example.com/person/1",
        name="John Doe",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    note = APNote(
        id="https://example.com/note/123",
        content="Hello, World!"
    )
    activity = APCreate(
        id="https://example.com/activity/123",
        actor=author,
        object=note,
        to=["https://www.w3.org/ns/activitystreams#Public"]
    )
    assert activity.type == "Create"
    assert activity.is_public()
    assert isinstance(activity.object, APNote)

def test_like_and_announce_interaction():
    """Test liking and announcing an object."""
    original_note = APNote(
        id="https://example.com/note/123",
        content="Original content"
    )
    liker = APPerson(
        id="https://example.com/person/1",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    announcer = APPerson(
        id="https://example.com/person/2",
        inbox="https://example.com/person/2/inbox",
        outbox="https://example.com/person/2/outbox"
    )
    
    like = APLike(
        id="https://example.com/activity/like/123",
        actor=liker,
        object=original_note
    )
    announce = APAnnounce(
        id="https://example.com/activity/announce/123",
        actor=announcer,
        object=original_note
    )
    
    assert like.type == "Like"
    assert announce.type == "Announce"
    assert str(like.object.id) == str(original_note.id)
    assert str(announce.object.id) == str(original_note.id)

def test_follow_with_collections():
    """Test following relationship with collections."""
    follower = APPerson(
        id="https://example.com/person/1",
        name="Follower",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox",
        following="https://example.com/person/1/following",
        followers="https://example.com/person/1/followers"
    )
    followed = APPerson(
        id="https://example.com/person/2",
        name="Followed",
        inbox="https://example.com/person/2/inbox",
        outbox="https://example.com/person/2/outbox",
        following="https://example.com/person/2/following",
        followers="https://example.com/person/2/followers"
    )
    
    follow = APFollow(
        id="https://example.com/activity/follow/123",
        actor=follower,
        object=followed
    )
    
    assert follow.type == "Follow"
    assert str(follow.actor.id) == str(follower.id)
    assert str(follow.object.id) == str(followed.id)
    assert follower.following is not None
    assert followed.followers is not None

def test_mention_in_content():
    """Test mentioning users in content with links."""
    mentioned = APPerson(
        id="https://example.com/person/1",
        name="John Doe",
        preferred_username="john",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    
    mention = APMention(
        id="https://example.com/mention/123",
        href=mentioned.id,
        name=f"@{mentioned.preferred_username}"
    )
    
    note = APNote(
        id="https://example.com/note/123",
        content=f"Hello {mention.name}!",
        tag=[mention]
    )
    
    assert mention in note.tag
    assert mention.name in note.content
    assert str(mention.href) == str(mentioned.id)

def test_collection_pagination_interaction():
    """Test interaction between collections and their pages."""
    items = [
        APNote(
            id=f"https://example.com/note/{i}",
            content=f"Note {i}"
        ) for i in range(1, 11)
    ]
    
    collection = APOrderedCollection(
        id="https://example.com/collection/123",
        total_items=len(items),
        ordered_items=items[:5]  # First page
    )
    
    page = APOrderedCollectionPage(
        id="https://example.com/collection/123/page/1",
        part_of=collection.id,
        ordered_items=items[5:],  # Second page
        start_index=5
    )
    
    assert collection.total_items == 10
    assert len(collection.ordered_items) == 5
    assert len(page.ordered_items) == 5
    assert page.start_index == 5

def test_actor_relationships():
    """Test complex relationships between actors."""
    organization = APOrganization(
        id="https://example.com/org/1",
        name="Example Org",
        inbox="https://example.com/org/1/inbox",
        outbox="https://example.com/org/1/outbox"
    )
    
    group = APGroup(
        id="https://example.com/group/1",
        name="Dev Team",
        inbox="https://example.com/group/1/inbox",
        outbox="https://example.com/group/1/outbox"
    )
    
    member = APPerson(
        id="https://example.com/person/1",
        name="John Developer",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    
    relationship = APRelationship(
        id="https://example.com/relationship/1",
        subject=member.id,
        object=group.id,
        relationship="member"
    )
    
    assert relationship.relationship == "member"
    assert str(relationship.subject) == str(member.id)
    assert str(relationship.object) == str(group.id)

def test_content_with_multiple_attachments():
    """Test creating content with multiple types of attachments."""
    image = APImage(
        id="https://example.com/image/1",
        url="https://example.com/image.jpg",
        width=800,
        height=600
    )
    
    document = APDocument(
        id="https://example.com/document/1",
        name="Specification",
        url="https://example.com/spec.pdf"
    )
    
    note = APNote(
        id="https://example.com/note/1",
        content="Check out these attachments!",
        attachment=[image, document]
    )
    
    assert len(note.attachment) == 2
    assert isinstance(note.attachment[0], APImage)
    assert isinstance(note.attachment[1], APDocument)

def test_event_series():
    """Test creating a series of related events."""
    venue = APPlace(
        id="https://example.com/place/1",
        name="Conference Center",
        latitude=51.5074,
        longitude=-0.1278
    )
    
    events = [
        APEvent(
            id=f"https://example.com/event/{i}",
            name=f"Workshop Day {i}",
            location=venue,
            start_time=(datetime.now() + timedelta(days=i)).isoformat(),
            end_time=(datetime.now() + timedelta(days=i, hours=2)).isoformat()
        ) for i in range(1, 4)
    ]
    
    collection = APOrderedCollection(
        id="https://example.com/collection/workshop-series",
        name="Workshop Series",
        ordered_items=events
    )
    
    assert len(collection.ordered_items) == 3
    assert all(isinstance(event, APEvent) for event in collection.ordered_items)
    assert all(event.location.id == venue.id for event in collection.ordered_items)

def test_nested_replies():
    """Test handling nested replies to content."""
    original_note = APNote(
        id="https://example.com/note/1",
        content="Original post"
    )
    
    reply1 = APNote(
        id="https://example.com/note/2",
        content="First reply",
        in_reply_to=str(original_note.id)
    )
    
    reply2 = APNote(
        id="https://example.com/note/3",
        content="Reply to reply",
        in_reply_to=str(reply1.id)
    )
    
    assert str(reply1.in_reply_to) == str(original_note.id)
    assert str(reply2.in_reply_to) == str(reply1.id)

def test_activity_chain():
    """Test a chain of related activities."""
    author = APPerson(
        id="https://example.com/person/1",
        name="Author",
        inbox="https://example.com/person/1/inbox",
        outbox="https://example.com/person/1/outbox"
    )
    
    # Create a note
    note = APNote(
        id="https://example.com/note/1",
        content="Original content"
    )
    
    create = APCreate(
        id="https://example.com/activity/1",
        actor=author,
        object=note
    )
    
    # Update the note
    note.content = "Updated content"
    update = APUpdate(
        id="https://example.com/activity/2",
        actor=author,
        object=note
    )
    
    # Delete the note
    delete = APDelete(
        id="https://example.com/activity/3",
        actor=author,
        object=note.id
    )
    
    # Undo the deletion
    undo = APUndo(
        id="https://example.com/activity/4",
        actor=author,
        object=delete
    )
    
    assert create.type == "Create"
    assert update.type == "Update"
    assert delete.type == "Delete"
    assert undo.type == "Undo"
    assert str(undo.object.id) == str(delete.id)
