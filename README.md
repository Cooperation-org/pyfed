# !!! THIS IS A COPY FROM THE PYFED ON GITLAB, LATEST VERSION SHOULD BE IN THERE. CHECK OUT [PYFED GITLAB](https://dev.funkwhale.audio/funkwhale/pyfed)

# PyFed

A robust, type-safe ActivityPub federation library for Python.

## Features

- Complete ActivityPub protocol implementation
- Type-safe models using Pydantic
- Flexible storage backends (SQL, Redis)
- Comprehensive security features
- Framework-agnostic design
- Async-first architecture

## Installation

```bash
pip install pyfed
```

#### Quick Start
```python
from pyfed.federation import FederationProtocol
from pyfed.models import APActivity, APActor

# Initialize federation handler
federation = FederationProtocol()

# Handle incoming activities
@federation.on_activity("Create")
async def handle_create(activity: APActivity):
    await federation.store_object(activity.object)
```

#### Documentation
- [Getting Started](docs/getting-started.md)
- [Configuration Guide](docs/configuration.md)
- [Architecture Overview](docs/architecture.md)
- [Security Guide](docs/security.md)
- [API Reference](docs/api/)
- [Testing Guide](tests/README.md)
- [Running an Example](examples/README.md)

#### Requirements
- Python 3.9+
- PostgreSQL (recommended) or SQLite
- Redis (optional, for caching)