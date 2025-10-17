"""
Anti-Filter Bridge - A secure tunnel to bypass internet restrictions

This package provides a WebSocket-based tunnel that can be used to bypass
internet restrictions by routing traffic through a secure WebSocket connection.
"""

__version__ = "0.1.0"
__author__ = "Your Name <your.email@example.com>"
__license__ = "MIT"

# Import key components for easier access
from .server import TunnelServer, create_ssl_context

# Client is in the root directory, not in this package
try:
    from .client import TunnelClient, create_client_ssl_context
except ImportError:
    # Fallback: client is in the root directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client import TunnelClient, create_client_ssl_context

__all__ = [
    'TunnelServer',
    'TunnelClient',
    'create_ssl_context',
    'create_client_ssl_context',
    '__version__',
]
