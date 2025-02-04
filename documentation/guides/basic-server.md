# Building a Basic ActivityPub Server with PyFed

This guide walks you through creating a basic ActivityPub-compatible server using PyFed. You'll learn how to set up endpoints, handle activities, and implement federation.

## Prerequisites

- Python 3.9+
- PyFed library installed (`pip install pyfed`)
- Basic understanding of ActivityPub protocol
- A domain name (for federation)

## Basic Server Setup

### 1. Project Structure

Create a new project with the following structure:
myserver/
├── config.yaml
├── main.py
├── handlers/
│ └── init.py
└── models/
    └── init.py

### 2. Basic Configuration

Create `config.yaml`:
```yaml
domain: "example.com"
database:
  url: "sqlite:///app.db"
keys:
  path: "./keys"
  rotation_interval: 30
server:
  host: "0.0.0.0"
  port: 8000
```

### 3. Basic Server Implementation

In `main.py`,

```python 
from pyfed import Server, ActivityHandler
from pyfed.models import APActivity
from typing import Optional

class MyActivityHandler(ActivityHandler):
    async def handle_follow(self, activity: APActivity) -> Optional[APActivity]:
        # Accept all follow requests
        return {
            "type": "Accept",
            "actor": self.server.actor_id,
            "object": activity
        }

async def main():
    # Create server instance
    server = Server(
        config_path="config.yaml",
        handler_class=MyActivityHandler
    )
    
    # Initialize server
    await server.initialize()
    
    # Start server
    await server.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Core Components
1. Actor Setup
Define your server's actor profile:

```python
actor_info = {
    "type": "Application",
    "name": "My ActivityPub Server",
    "summary": "A basic ActivityPub server using PyFed",
    "preferredUsername": "myserver",
    "inbox": "/inbox",
    "outbox": "/outbox",
    "followers": "/followers",
    "following": "/following"
}

server = Server(
    config_path="config.yaml",
    handler_class=MyActivityHandler,
    actor_info=actor_info
)
```

2. Activity Handling
Implement custom activity handlers:

```python
class MyActivityHandler(ActivityHandler):
    async def handle_create(self, activity: Activity) -> Optional[Activity]:
        # Handle Create activities
        object_type = activity.get("object", {}).get("type")
        if object_type == "Note":
            await self.store_note(activity["object"])
        return None
    
    async def handle_like(self, activity: Activity) -> Optional[Activity]:
        # Handle Like activities
        await self.store_like(activity)
        return None
    
    async def store_note(self, note):
        # Store note in database
        await self.server.db.notes.insert(note)
    
    async def store_like(self, like):
        # Store like in database
        await self.server.db.likes.insert(like)
```

3. Database Models
Create models in models/__init__.py:

```python
from pyfed.models import BaseModel
from datetime import datetime
from typing import Optional

class Note(BaseModel):
    content: str
    published: datetime
    attributed_to: str
    to: list[str]
    cc: Optional[list[str]] = None

class Like(BaseModel):
    actor: str
    object: str
    published: datetime
```

Federation Features
1. Webfinger Support
Enable Webfinger for user discovery:

```python
from pyfed.protocols import WebFinger

webfinger = WebFinger(domain="example.com")
server.add_protocol(webfinger)
```

2. HTTP Signatures
Configure HTTP signatures for secure federation:

```python
from pyfed.security import HTTPSignatureVerifier

server.configure_signatures(
    key_id="https://example.com/actor#main-key",
    private_key_path="keys/private.pem"
)
```

3. Activity Distribution
Implement activity distribution:

```python
class MyActivityHandler(ActivityHandler):
    async def handle_create(self, activity: Activity) -> Optional[Activity]:
        # Store the activity
        await self.store_note(activity["object"])
        
        # Distribute to followers
        followers = await self.get_followers()
        await self.distribute_activity(activity, followers)
        
        return None
    
    async def distribute_activity(self, activity: Activity, recipients: list[str]):
        for recipient in recipients:
            await self.server.deliver_activity(
                activity=activity,
                recipient=recipient
            )
```

## Running the Server
1. Generate keys:

```bash
python -m pyfed.tools.keygen keys/
```

2. Start the server:

```bash
python main.py
```

3. Testing Federation
Test Webfinger:

```bash 
curl https://example.com/.well-known/webfinger?resource=acct:myserver@example.com
```

2. Test Actor Profile:

```bash
curl -H "Accept: application/activity+json" https://example.com/actor
```

3. Send a Follow Activity:

```bash
curl -X POST https://example.com/inbox \
  -H "Content-Type: application/activity+json" \
  -d '{
    "type": "Follow",
    "actor": "https://other-server.com/users/alice",
    "object": "https://example.com/actor"
  }'
  ```

Security Considerations
1. Always verify HTTP signatures
2. Validate activities before processing
3. Implement rate limiting
4. Use HTTPS in production
5. Regularly rotate keys

Next Steps
- Implement more activity types
- Add user authentication
- Set up media handling
- Add moderation features
- Implement caching

See Also
- [Security Guide](../security.md)
- [API Reference](../api)