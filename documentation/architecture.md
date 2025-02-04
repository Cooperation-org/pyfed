# PyFed Architecture Guide

## Overview
PyFed is a modular, type-safe ActivityPub federation library designed for Python applications. It provides a comprehensive implementation of the ActivityPub protocol with a focus on security, extensibility, and developer experience.

## Core Architecture

### Component Layers

┌─────────────────────────────────────────────────────┐
│ Application Layer                                   │
│ (Your ActivityPub Application)                      │
├─────────────────────────────────────────────────────┤
│ PyFed Library                                       │
├───────────┬───────────┬──────────────┬─────────────┤
│ Servers   │ Models    │ Handlers     │ Federation  │
├───────────┼───────────┼──────────────┼─────────────┤
│ Security  │ Storage   │ Serializers  │ Cache       │
└───────────┴───────────┴──────────────┴─────────────┘

### Core Components

1. **Servers**
   - Inbox/Outbox handlers
   - Request processing
   - Activity routing
   - Federation endpoints

2. **Models**
   - ActivityPub objects
   - Actors and activities
   - Collections
   - Type-safe validation

3. **Handlers**
   - Activity processing
   - Content validation
   - Federation logic
   - State management

4. **Federation**
   - Protocol implementation
   - Activity delivery
   - Remote interaction
   - Federation rules

5. **Security**
   - HTTP signatures
   - Request validation
   - Permission checks
   - SSL/TLS handling

6. **Storage**
   - Activity persistence
   - Object storage
   - Collection management
   - Query interfaces

7. **Serializers**
   - JSON-LD handling
   - Data transformation
   - Schema validation
   - Format conversion

8. **Cache**
   - Object caching
   - Request caching
   - Performance optimization
   - Cache invalidation

## Data Flow

### Incoming Activity Flow

- Remote Server → Inbox Handler: Remote server sends an ActivityPub activity to your inbox endpoint
- Inbox Handler → Signature Check: Validates HTTP signatures using the sender's public key
- Signature Check → Activity Parser: Parses and validates the JSON activity data
- Activity Parser → Activity Handler: Routes to appropriate handler based on activity type
- Activity Handler → Storage: Stores the validated activity
- Storage → Activity Handler: Confirms storage completion
- Activity Handler → Response: Generates appropriate response (Accept/Reject)


### Outgoing Activity Flow

- Local Actor → Outbox Handler: Local user/system initiates an activity
- Outbox Handler → Activity Creator: Creates the ActivityPub JSON object
- Activity Creator → Activity Signer: Signs the activity with the local actor's private key
- Activity Signer → Storage: Stores the signed activity
- Storage → Delivery Queue: Queues the activity for delivery
- Delivery Queue → Activity Sender: Manages delivery attempts and retries
- Activity Sender → Remote Server: Delivers the activity to recipient inboxes


## Key Design Principles

### 1. Type Safety
- Comprehensive type hints
- Pydantic model validation
- Runtime type checking
- Schema enforcement

### 2. Modularity
- Independent components
- Clear interfaces
- Pluggable backends
- Extensible design

### 3. Security First
- Signature verification
- Request validation
- Permission checks
- Secure defaults

### 4. Performance
- Efficient caching
- Async operations
- Batch processing
- Resource optimization

## Component Details

### Server Components
```python
# Server initialization
server = ActivityPubServer(
    storage=SQLStorageBackend(),
    delivery=ActivityDelivery(),
    protocol=FederationProtocol(),
    security=SecurityManager()
)

# Request handling
@server.route("/inbox")
async def handle_inbox(request):
    await server.inbox_handler.handle_request(request)
```

### Model System
```python
# Type-safe model definition
class APNote(APObject):
    type: Literal["Note"]
    content: str
    attributedTo: Union[str, APActor]
    to: List[str]
    cc: Optional[List[str]] = None
```

### Handler System
```python
# Activity handler
class CreateHandler(ActivityHandler):
    async def validate(self, activity: Dict[str, Any]) -> None:
        # Validation logic
        pass
        
    async def process(self, activity: Dict[str, Any]) -> None:
        # Processing logic
        pass
```

### Storage System
```python
# Storage operations
class SQLStorageBackend(BaseStorageBackend):
    async def create_activity(self, activity: Dict[str, Any]) -> str:
        # Store activity
        pass
        
    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        # Retrieve object
        pass
```

### Configuration
#### Basic Configuration

```python
config = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": False
    },
    "federation": {
        "domain": "example.com",
        "https_required": True,
        "max_payload_size": 1048576
    },
    "security": {
        "key_size": 2048,
        "signature_algorithm": "rsa-sha256",
        "signature_timeout": 300
    },
    "storage": {
        "backend": "sql",
        "dsn": "postgresql://user:pass@localhost/dbname"
    },
    "cache": {
        "backend": "redis",
        "url": "redis://localhost",
        "ttl": 3600
    }
}
```

#### Advanced Configuration

```python
config = {
    "federation": {
        "delivery": {
            "max_attempts": 5,
            "retry_delay": 300,
            "timeout": 30
        },
        "collections": {
            "page_size": 20,
            "max_items": 5000
        }
    },
    "security": {
        "allowed_algorithms": ["rsa-sha256", "hs2019"],
        "key_rotation": {
            "enabled": True,
            "interval": 7776000  # 90 days
        }
    }
}
```

Integration Points
Application Integration
# Initialize PyFed
```python
pyfed = PyFed(config)
```

# Register handlers
```python
pyfed.register_handler("Create", CustomCreateHandler)
pyfed.register_handler("Follow", CustomFollowHandler)
```

# Start server
```python
await pyfed.start()
```

###  Storage Integration

```python
# Custom storage backend
class CustomStorage(BaseStorageBackend):
    async def create_activity(self, activity):
        # Custom storage logic
        pass
        
    async def get_object(self, object_id):
        # Custom retrieval logic
        pass

# Register storage
pyfed.use_storage(CustomStorage())
```

Best Practices

### Security
- Always verify HTTP signatures
- Validate all incoming activities
- Use HTTPS for all federation
- Implement rate limiting

### Performance
- Use appropriate caching
- Implement batch processing
- Handle async operations properly
- Monitor resource usage

### Reliability
- Implement retry logic
- Handle failures gracefully
- Log important operations
- Monitor system health

#### See Also
- [Models API Reference](../api/models.md)
- [Security Guide](../security.md)