# PyFed Configuration Guide

## Overview
PyFed provides flexible configuration options through environment variables, configuration files (YAML/JSON), and programmatic configuration. This guide covers all available configuration options and best practices.

## Configuration Methods

### 1. Environment Variables
All configuration options can be set using environment variables with the `PYFED_` prefix:

```bash
# Core settings
PYFED_DOMAIN=example.com
PYFED_DEBUG=false

# Database settings
PYFED_DATABASE_URL=postgresql://user:pass@localhost/dbname
PYFED_DB_MIN_CONNECTIONS=5
PYFED_DB_MAX_CONNECTIONS=20
PYFED_DB_TIMEOUT=30

# Security settings
PYFED_KEY_PATH=keys
PYFED_SIGNATURE_TTL=300

# Federation settings
PYFED_SHARED_INBOX=true
PYFED_DELIVERY_TIMEOUT=30
PYFED_VERIFY_SSL=true

# Media settings
PYFED_UPLOAD_PATH=uploads
PYFED_MAX_UPLOAD_SIZE=10000000
```

## 2. Configuration File
Configuration can be loaded from YAML or JSON files:

```yaml
# config.yaml
domain: example.com
debug: false

storage:
  provider: postgresql
  database:
    url: postgresql://user:pass@localhost/dbname
    min_connections: 5
    max_connections: 20
    timeout: 30

security:
  key_path: keys
  signature_ttl: 300
  allowed_algorithms:
    - rsa-sha256
    - hs2019

federation:
  shared_inbox: true
  delivery_timeout: 30
  verify_ssl: true

media:
  upload_path: uploads
  max_size: 10000000
  allowed_types:
    - image/jpeg
    - image/png
    - image/gif
    - video/mp4
    - audio/mpeg
```

3. Programmatic Configuration
Configure PyFed directly in your code:

```python
from pyfed.config import PyFedConfig, DatabaseConfig, SecurityConfig

config = PyFedConfig(
    domain="example.com",
    storage=StorageConfig(
        provider="postgresql",
        database=DatabaseConfig(
            url="postgresql://user:pass@localhost/dbname",
            min_connections=5,
            max_connections=20,
            timeout=30
        )
    ),
    security=SecurityConfig(
        key_path="keys",
        signature_ttl=300
    )
)
```

Configuration Options
Core Settings
| Option | Environment Variable | Default | Description | 
|--------|---------------------|---------|-------------| 
| domain | PYFED_DOMAIN | localhost | Server domain name | 
| debug | PYFED_DEBUG | false | Enable debug mode |

Storage Settings
| Option | Environment Variable | Default | Description | 
|--------|---------------------|---------|-------------| 
| storage.provider | PYFED_STORAGE_PROVIDER | sqlite | Storage backend (sqlite/postgresql) | 
| storage.database.url | PYFED_DATABASE_URL | sqlite:///pyfed.db | Database connection URL | 
| storage.database.min_connections | PYFED_DB_MIN_CONNECTIONS | 5 | Minimum database connections | 
| storage.database.max_connections | PYFED_DB_MAX_CONNECTIONS | 20 | Maximum database connections | 
| storage.database.timeout | PYFED_DB_TIMEOUT | 30 | Database connection timeout |

Security Settings
| Option | Environment Variable | Default | Description | 
|--------|---------------------|---------|-------------| 
| security.key_path | PYFED_KEY_PATH | keys | Path to key storage | 
| security.signature_ttl | PYFED_SIGNATURE_TTL | 300 | Signature time-to-live (seconds) | 
| security.allowed_algorithms | - | ["rsa-sha256"] | Allowed signature algorithms |

Federation Settings
| Option | Environment Variable | Default | Description | 
|--------|---------------------|---------|-------------| 
| federation.shared_inbox | PYFED_SHARED_INBOX | true | Enable shared inbox | 
| federation.delivery_timeout | PYFED_DELIVERY_TIMEOUT | 30 | Activity delivery timeout | 
| federation.verify_ssl | PYFED_VERIFY_SSL | true | Verify SSL certificates |

Media Settings
| Option | Environment Variable | Default | Description | 
|--------|---------------------|---------|-------------| 
| media.upload_path | PYFED_UPLOAD_PATH | uploads | Media upload directory | 
| media.max_size | PYFED_MAX_UPLOAD_SIZE | 10000000 | Maximum upload size (bytes) | 
| media.allowed_types | - | [image/*, video/mp4, audio/mpeg] | Allowed media types |

Best Practices
1. Environment-Specific Configuration
Use different configuration files for development, testing, and production:

# Development
config.dev.yaml

# Testing
config.test.yaml

# Production
config.prod.yaml

2. Secure Secrets
Never commit sensitive information to version control
Use environment variables for secrets in production
Keep keys and credentials secure
3. Validation
PyFed validates all configuration options. Invalid configurations will raise ConfigError with detailed error messages.

4. Logging
Configure logging for better debugging:

```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - console
    - file
```

5. Performance Tuning
Optimize database and cache settings based on your requirements:

```yaml
storage:
  database:
    min_connections: 5
    max_connections: 20
    timeout: 30

cache:
  backend: redis
  url: redis://localhost
  ttl: 3600
```

Framework Integration
Flask Integration
from pyfed.integration.frameworks.flask import FlaskIntegration

integration = FlaskIntegration(config)
await integration.initialize()

Django Integration
from pyfed.integration.frameworks.django import DjangoIntegration

integration = DjangoIntegration(config)
await integration.initialize()

Error Handling
PyFed provides detailed error messages for configuration issues:

```python
try:
    config = PyFedConfig.from_file("config.yaml")
except ConfigError as e:
    logger.error(f"Configuration error: {e}")
```

### See Also
- [Server API Reference](../api/server.md)
- [Models API Reference](../api/models.md)
- [Handlers API Reference](../api/handlers.md)