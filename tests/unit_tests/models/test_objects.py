"""
test_models.py
This module contains tests for the ActivityPub models.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from pyfed.models import (
    APObject, APEvent, APPlace, APProfile, APRelationship, APTombstone,
    APArticle, APAudio, APDocument, APImage, APNote, APPage, APVideo
)

def test_valid_ap_object():
    ap_object = APObject(
        id="https://example.com/object/123",
        type="Object",
        content="Sample content"
    )
    assert str(ap_object.id) == "https://example.com/object/123"
    assert ap_object.type == "Object"
    assert ap_object.content == "Sample content"

def test_invalid_ap_object_missing_type():
    with pytest.raises(ValidationError):
        APObject(id="123", content="Sample content")

def test_ap_object_with_optional_fields():
    ap_object = APObject(
        id="https://example.com/object/123",
        type="Object",
        content="Sample content",
        name="Test Object",
        published=datetime.now().isoformat(),
        updated=datetime.now().isoformat(),
        to=["https://example.com/user/1", "https://example.com/user/2"]
    )
    assert ap_object.name is not None
    assert ap_object.published is not None
    assert ap_object.updated is not None
    assert isinstance(ap_object.to, list)

def test_ap_object_is_public():
    public_object = APObject(
        id="https://example.com/object/123",
        type="Object",
        to=["https://www.w3.org/ns/activitystreams#Public"]
    )
    assert public_object.is_public()

    private_object = APObject(
        id="https://example.com/object/124",
        type="Object",
        to=["https://example.com/user/1"]
    )
    assert not private_object.is_public()

@pytest.mark.parametrize("content", [
    "",
    "a" * 5001,
    "<p>This is <strong>HTML</strong> content</p>",
])
def test_ap_object_content_edge_cases(content):
    ap_object = APObject(
        id="https://example.com/object/123",
        type="Object",
        content=content
    )
    assert ap_object.content == content

def test_ap_object_get_mentions():
    ap_object = APObject(
        id="https://example.com/object/123",
        type="Object",
        tag=[
            {"type": "Mention", "href": "https://example.com/user/1"},
            {"type": "Mention", "href": "https://example.com/user/2"},
            {"type": "Hashtag", "href": "https://example.com/tag/test"}
        ]
    )
    mentions = ap_object.get_mentions()
    assert len(mentions) == 2
    assert "https://example.com/user/1" in mentions
    assert "https://example.com/user/2" in mentions

def test_valid_ap_event():
    ap_event = APEvent(
        id="https://example.com/event/123",
        content="Event content",
        start_time=datetime.now().isoformat(),
        end_time=(datetime.now() + timedelta(hours=2)).isoformat()
    )
    assert ap_event.type == "Event"

def test_ap_event_invalid_end_time():
    with pytest.raises(ValidationError):
        APEvent(
            id="https://example.com/event/123",
            content="Event content",
            start_time="2024-01-01T10:00:00Z",
            end_time="2024-01-01T09:00:00Z"
        )

def test_ap_event_with_place():
    place = APPlace(
        id="https://example.com/place/123",
        name="Event Venue",
        latitude=52.5200,
        longitude=13.4050
    )
    event = APEvent(
        id="https://example.com/event/123",
        name="Test Event",
        location=place
    )
    assert str(event.location.id) == "https://example.com/place/123"
    assert event.location.name == "Event Venue"

def test_valid_ap_place():
    ap_place = APPlace(
        id="https://example.com/place/123",
        name="Test Place",
        latitude=52.5200,
        longitude=13.4050,
        units="km"
    )
    assert ap_place.type == "Place"
    assert ap_place.latitude == 52.5200
    assert ap_place.longitude == 13.4050

def test_ap_place_invalid_units():
    with pytest.raises(ValidationError):
        APPlace(
            id="https://example.com/place/123",
            name="Test Place",
            latitude=52.5200,
            longitude=13.4050,
            units="invalid_unit"
        )

def test_ap_place_invalid_latitude():
    with pytest.raises(ValidationError):
        APPlace(
            id="https://example.com/place/123",
            name="Test Place",
            latitude=91,  # Invalid latitude
            longitude=13.4050
        )

def test_valid_ap_profile():
    ap_profile = APProfile(
        id="https://example.com/profile/123",
        describes="https://example.com/user/123",
        name="John Doe"
    )
    assert ap_profile.type == "Profile"
    assert ap_profile.describes == "https://example.com/user/123"

def test_valid_ap_relationship():
    ap_relationship = APRelationship(
        id="https://example.com/relationship/123",
        subject="https://example.com/user/1",
        object="https://example.com/user/2",
        relationship="friend"
    )
    assert ap_relationship.type == "Relationship"
    assert ap_relationship.relationship == "friend"

def test_valid_ap_tombstone():
    ap_tombstone = APTombstone(
        id="https://example.com/tombstone/123",
        former_type="Article",
        deleted=datetime.now().isoformat()
    )
    assert ap_tombstone.type == "Tombstone"
    assert ap_tombstone.former_type == "Article"

def test_valid_ap_article():
    ap_article = APArticle(
        id="https://example.com/article/123",
        name="Test Article",
        content="This is a test article content."
    )
    assert ap_article.type == "Article"

def test_valid_ap_audio():
    ap_audio = APAudio(
        id="https://example.com/audio/123",
        name="Test Audio",
        url="https://example.com/audio/123.mp3",
        duration="PT2M30S"
    )
    assert ap_audio.type == "Audio"

def test_valid_ap_document():
    ap_document = APDocument(
        id="https://example.com/document/123",
        name="Test Document",
        url="https://example.com/document/123.pdf"
    )
    assert ap_document.type == "Document"

def test_valid_ap_image():
    ap_image = APImage(
        id="https://example.com/image/123",
        name="Test Image",
        url="https://example.com/image/123.jpg",
        width=1920,
        height=1080
    )
    assert ap_image.type == "Image"
    assert ap_image.width == 1920
    assert ap_image.height == 1080

def test_ap_image_invalid_dimensions():
    with pytest.raises(ValidationError):
        APImage(
            id="https://example.com/image/123",
            name="Test Image",
            url="https://example.com/image/123.jpg",
            width=-1,
            height=1080
        )

def test_valid_ap_note():
    ap_note = APNote(
        id="https://example.com/note/123",
        content="This is a test note."
    )
    assert ap_note.type == "Note"

def test_valid_ap_page():
    ap_page = APPage(
        id="https://example.com/page/123",
        name="Test Page",
        content="This is a test page content."
    )
    assert ap_page.type == "Page"

def test_valid_ap_video():
    ap_video = APVideo(
        id="https://example.com/video/123",
        name="Test Video",
        url="https://example.com/video/123.mp4",
        duration="PT1H30M",
        media_type="video/mp4"
    )
    assert ap_video.type == "Video"

def test_ap_video_invalid_media_type():
    with pytest.raises(ValidationError):
        APVideo(
            id="https://example.com/video/123",
            name="Test Video",
            url="https://example.com/video/123.mp4",
            duration="PT1H30M",
            media_type="image/jpg"  # Invalid media type for video
        )
