# Anti-Filter Bridge - Project Specification

## Overview

Anti-Filter Bridge is a secure tunneling solution designed to bypass internet restrictions using WebSockets. This document outlines the project's specifications, architecture, and implementation details.

## Table of Contents

1. [Requirements](requirements.md)
2. [Architecture](architecture.md)
3. [Protocols](protocols.md)
4. [Security](security.md)
5. [Deployment](deployment.md)
6. [Maintenance](maintenance.md)
7. [Troubleshooting](troubleshooting.md)

## Project Structure

```
anti_filter_bridge/
├── anti_filter_bridge/  # Core package
│   ├── __init__.py
│   ├── client.py        # Client implementation
│   └── server.py        # Server implementation
├── scripts/             # Utility scripts
│   ├── __init__.py
│   ├── afb_utils.py     # Service management
│   ├── config_generator.py
│   └── monitor.py
├── tests/               # Test suite
│   ├── test_performance.py
│   └── test_security.py
├── examples/            # Usage examples
├── certs/               # SSL/TLS certificates
├── logs/                # Log files
└── specs/               # This specification
```

## Version History

- **0.1.0 (2025-09-29)**: Initial project structure and core functionality

## Contributing

Please refer to the main project README for contribution guidelines.
