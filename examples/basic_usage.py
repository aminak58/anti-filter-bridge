"""
Basic usage example for Anti-Filter Bridge.

This example shows how to use the Anti-Filter Bridge to create a secure tunnel
between a client and server.
"""
import asyncio
import logging
import ssl
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('Example')

# Import the Anti-Filter Bridge components
from anti_filter_bridge import (
    TunnelServer, TunnelClient,
    create_ssl_context, create_client_ssl_context
)

# Configuration
HOST = '127.0.0.1'
PORT = 8443
SOCKS_PORT = 1080
CERT_DIR = Path('certs')
CERT_FILE = CERT_DIR / 'cert.pem'
KEY_FILE = CERT_DIR / 'key.pem'

async def run_example():
    """Run the basic usage example."""
    logger.info("Starting Anti-Filter Bridge example...")
    
    # Create SSL context for the server
    ssl_context = create_ssl_context(CERT_FILE, KEY_FILE)
    
    # Create and start the server
    server = TunnelServer(
        host=HOST,
        port=PORT,
        ssl_context=ssl_context
    )
    
    # Create and start the client
    client_ssl_context = create_client_ssl_context()
    client_ssl_context.check_hostname = False
    client_ssl_context.verify_mode = ssl.CERT_NONE  # For testing only
    
    client = TunnelClient(
        server_uri=f"wss://{HOST}:{PORT}",
        local_port=SOCKS_PORT,
        ssl_context=client_ssl_context
    )
    
    # Start both server and client
    server_task = asyncio.create_task(server.start())
    client_task = asyncio.create_task(client.run())
    
    try:
        # Give them time to start
        await asyncio.sleep(2)
        
        logger.info("Tunnel is running!")
        logger.info(f"  - Server: wss://{HOST}:{PORT}")
        logger.info(f"  - SOCKS5 Proxy: 127.0.0.1:{SOCKS_PORT}")
        logger.info("\nPress Ctrl+C to stop the tunnel...")
        
        # Keep the example running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Clean up
        server_task.cancel()
        client_task.cancel()
        
        await asyncio.gather(
            server_task,
            client_task,
            return_exceptions=True
        )
        
        await asyncio.gather(
            server.stop(),
            client.stop(),
            return_exceptions=True
        )
        
        logger.info("Example completed")

if __name__ == "__main__":
    # Make sure the certificate files exist
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        logger.error("Certificate files not found. Please run 'python generate_certs.py' first.")
        sys.exit(1)
    
    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("\nExample stopped by user")
