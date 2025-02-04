"""
test_actors.py
This module contains tests for the Actor types in ActivityPub.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from pyfed.models import (
    APPerson, APGroup, APOrganization, APApplication, APService
)

def test_valid_person():
    person = APPerson(
        id="https://example.com/users/alice",
        name="Alice",
        inbox="https://example.com/users/alice/inbox",
        outbox="https://example.com/users/alice/outbox",
        preferred_username="alice"
    )
    assert person.type == "Person"
    assert str(person.inbox) == "https://example.com/users/alice/inbox"
    assert str(person.outbox) == "https://example.com/users/alice/outbox"
    print(person.preferred_username)
    assert person.preferred_username == "alice"

def test_person_with_optional_fields():
    person = APPerson(
        id="https://example.com/users/alice",
        name="Alice",
        inbox="https://example.com/users/alice/inbox",
        outbox="https://example.com/users/alice/outbox",
        following="https://example.com/users/alice/following",
        followers="https://example.com/users/alice/followers",
        liked="https://example.com/users/alice/liked",
        streams=["https://example.com/users/alice/stream1"]
    )
    assert str(person.following) == "https://example.com/users/alice/following"
    assert str(person.followers) == "https://example.com/users/alice/followers"
    assert str(person.liked) == "https://example.com/users/alice/liked"
    assert len(person.streams) == 1

def test_invalid_person_missing_required():
    with pytest.raises(ValidationError):
        APPerson(
            id="https://example.com/users/alice",
            name="Alice"
            # Missing required inbox and outbox
        )

def test_invalid_person_invalid_url():
    with pytest.raises(ValidationError):
        APPerson(
            id="https://example.com/users/alice",
            name="Alice",
            inbox="not-a-url",  # Invalid URL
            outbox="https://example.com/users/alice/outbox"
        )

def test_valid_group():
    group = APGroup(
        id="https://example.com/groups/admins",
        name="Administrators",
        inbox="https://example.com/groups/admins/inbox",
        outbox="https://example.com/groups/admins/outbox"
    )
    assert group.type == "Group"
    assert group.name == "Administrators"

def test_valid_organization():
    org = APOrganization(
        id="https://example.com/org/acme",
        name="ACME Corporation",
        inbox="https://example.com/org/acme/inbox",
        outbox="https://example.com/org/acme/outbox"
    )
    assert org.type == "Organization"
    assert org.name == "ACME Corporation"

def test_valid_application():
    app = APApplication(
        id="https://example.com/apps/bot",
        name="Bot Application",
        inbox="https://example.com/apps/bot/inbox",
        outbox="https://example.com/apps/bot/outbox"
    )
    assert app.type == "Application"
    assert app.name == "Bot Application"

def test_valid_service():
    service = APService(
        id="https://example.com/services/api",
        name="API Service",
        inbox="https://example.com/services/api/inbox",
        outbox="https://example.com/services/api/outbox"
    )
    assert service.type == "Service"
    assert service.name == "API Service"

def test_actor_with_public_key():
    person = APPerson(
        id="https://example.com/users/alice",
        name="Alice",
        inbox="https://example.com/users/alice/inbox",
        outbox="https://example.com/users/alice/outbox",
        public_key={
            "id": "https://example.com/users/alice#main-key",
            "owner": "https://example.com/users/alice",
            "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n..."
        }
    )
    assert person.public_key is not None
    assert "publicKeyPem" in person.public_key

def test_actor_with_endpoints():
    person = APPerson(
        id="https://example.com/users/alice",
        name="Alice",
        inbox="https://example.com/users/alice/inbox",
        outbox="https://example.com/users/alice/outbox",
        endpoints={
            "sharedInbox": "https://example.com/inbox",
            "oauthAuthorizationEndpoint": "https://example.com/oauth/authorize"
        }
    )
    assert person.endpoints is not None
    assert "sharedInbox" in person.endpoints
