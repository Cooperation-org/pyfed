# Getting Started with PyFed

## Overview
PyFed is a powerful, type-safe ActivityPub federation library for Python applications. This guide will help you get started with integrating PyFed into your application.

## Prerequisites
- Python 3.9 or higher
- PostgreSQL (recommended) or SQLite
- Redis (optional, for caching)

## Installation

```bash
pip install pyfed
```

Quick Start
1. Basic Setup
Create a new Python file (e.g., app.py):
```python
from pyfed import PyFedConfig
from pyfed.integration.frameworks.flask import FlaskIntegration
# or for Django:
# from pyfed.integration.frameworks.django import DjangoIntegration

# Create configuration
config = PyFedConfig(
    domain="example.com",
    storage=StorageConfig(
        provider="postgresql",
        database=DatabaseConfig(
            url="postgresql://user:pass@localhost/dbname",
            min_connections=5,
            max_connections=20
        )
    ),
    security=SecurityConfig(
        key_path="keys",
        signature_ttl=300
    )
)

# Initialize integration
integration = FlaskIntegration(config)
await integration.initialize()
```

2. Define an Actor
```python
from pyfed.models import APPerson

actor = APPerson(
    id="https://example.com/users/alice",
    name="Alice",
    preferredUsername="alice",
    inbox="https://example.com/users/alice/inbox",
    outbox="https://example.com/users/alice/outbox",
    followers="https://example.com/users/alice/followers",
    following="https://example.com/users/alice/following"
)
```

3. Handle Activities
```python
from pyfed.handlers import CreateHandler, FollowHandler

# Register activity handlers
@integration.handle_activity("Create")
async def handle_create(activity):
    handler = CreateHandler()
    await handler.handle(activity)

@integration.handle_activity("Follow")
async def handle_follow(activity):
    handler = FollowHandler()
    await handler.handle(activity)
```

4. Send Activities
```python
# Create a Note
note = APNote(
    id="https://example.com/notes/1",
    attributedTo="https://example.com/users/alice",
    content="Hello, ActivityPub world!",
    to=["https://www.w3.org/ns/activitystreams#Public"]
)

# Create and send activity
create_activity = APCreate(
    actor="https://example.com/users/alice",
    object=note,
    to=["https://www.w3.org/ns/activitystreams#Public"]
)

await integration.deliver_activity(
    activity=create_activity.serialize(),
    recipients=["https://example.com/users/bob"]
)
```

Configuration
Create a configuration file (config.yaml):
```yaml
domain: example.com
debug: false

storage:
  provider: postgresql
  database:
    url: postgresql://user:pass@localhost/dbname
    min_connections: 5
    max_connections: 20

security:
  key_path: keys
  signature_ttl: 300
  allowed_algorithms:
    - rsa-sha256

federation:
  shared_inbox: true
  delivery_timeout: 30
  verify_ssl: true

media:
  upload_path: uploads
  max_size: 10000000
```

Framework Integration
Flask Integration
```python
from flask import Flask
from pyfed.integration.frameworks.flask import FlaskIntegration

app = Flask(__name__)
integration = FlaskIntegration(config)

@app.route("/inbox", methods=["POST"])
async def inbox():
    return await integration.handle_inbox(request)

@app.route("/users/<username>", methods=["GET"])
async def actor(username):
    return await integration.handle_actor(username)

if __name__ == "__main__":
    app.run()
```

Django Integration

```python
# settings.py
INSTALLED_APPS = [
    ...
    'pyfed.integration.frameworks.django',
]

# urls.py
from django.urls import path
from pyfed.integration.frameworks.django import DjangoIntegration

integration = DjangoIntegration(config)

urlpatterns = [
    path('inbox/', integration.views['inbox'].as_view()),
    path('users/<str:username>/', integration.views['actor'].as_view()),
]
```

#### Basic Features
##### 1. Activity Types
PyFed supports all standard ActivityPub activity types:

- Create
- Update
- Delete
- Follow
- Like
- Announce
- Accept
- Reject
- Undo

##### 2. Object Types
Common object types include:

- Note
- Article
- Image
- Video
- Audio
- Person
- Group
- Organization

##### 3. Collections
Manage collections of objects:

- Collection
- OrderedCollection
- CollectionPage
- OrderedCollectionPage

#### Next Steps
Read the Configuration Guide for detailed configuration options
Explore the API Reference for comprehensive documentation
Check the Architecture Guide to understand PyFed's design
Join our community for support and discussions

#### Examples
Find more examples in our GitHub repository (in the [examples directory](../examples/README.md)):

- Basic ActivityPub server

Troubleshooting
Common Issues
1. Database Connection
```python
try:
    await integration.initialize()
except StorageError as e:
    logger.error(f"Database connection failed: {e}")
```

2. Activity Delivery
```python
try:
    await integration.deliver_activity(activity, recipients)
except DeliveryError as e:
    logger.error(f"Activity delivery failed: {e}")
```

3. Signature Verification
```python
try:
    await integration.verify_signature(request)
except DeliveryError as e:
    logger.error(f"Signature verification failed: {e}")
```