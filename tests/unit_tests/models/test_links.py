"""
test_links_models.py
This module contains tests for the Link types in ActivityPub.
"""
import pytest
from pydantic import ValidationError
from pyfed.models import APLink, APMention

def test_valid_link():
    """Test creating a valid Link object."""
    link = APLink(
        id="https://example.com/link/123",
        
        href="https://example.com/resource"
    )
    assert link.type == "Link"
    assert str(link.href) == "https://example.com/resource"

def test_link_with_optional_fields():
    """Test creating a Link with all optional fields."""
    link = APLink(
        id="https://example.com/link/123",
        
        href="https://example.com/resource",
        name="Test Link",
        hreflang="en",
        media_type="image/jpeg",
        width=800,
        height=600,
        preview="https://example.com/preview"
    )
    assert link.name == "Test Link"
    assert link.hreflang == "en"
    assert link.media_type == "image/jpeg"
    assert link.width == 800
    assert link.height == 600
    assert str(link.preview) == "https://example.com/preview"

def test_link_with_rel():
    """Test creating a Link with relationship fields."""
    link = APLink(
        id="https://example.com/link/123",
        href="https://example.com/resource",
        rel=["canonical", "alternate"]
    )
    assert "canonical" in link.rel
    assert "alternate" in link.rel

def test_valid_mention():
    """Test creating a valid Mention object."""
    mention = APMention(
        id="https://example.com/mention/123",
        href="https://example.com/user/alice",
        name="@alice"
    )
    assert mention.type == "Mention"
    assert str(mention.href) == "https://example.com/user/alice"
    assert mention.name == "@alice"

def test_invalid_link_missing_href():
    """Test that Link creation fails when href is missing."""
    with pytest.raises(ValidationError):
        APLink(
            id="https://example.com/link/123",
        )

def test_invalid_link_invalid_url():
    """Test that Link creation fails with invalid URLs."""
    with pytest.raises(ValidationError):
        APLink(
            id="https://example.com/link/123",
            href="not-a-url"
        )

def test_invalid_link_invalid_media_type():
    """Test that Link creation fails with invalid media type."""
    with pytest.raises(ValidationError):
        APLink(
            id="https://example.com/link/123",
            href="https://example.com/resource",
            media_type="invalid/type"
        )

def test_invalid_mention_wrong_type():
    """Test that Mention creation fails with wrong type."""
    with pytest.raises(ValidationError):
        APMention(
            id="https://example.com/mention/123",
            type="Link",  # Should be "Mention"
            href="https://example.com/user/alice"
        )
