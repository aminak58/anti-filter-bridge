"""
Run the Anti-Filter Bridge tunnel (client and server).

This script provides a simple way to run both the client and server
components for testing purposes.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from anti_filter_bridge import (
    TunnelServer, TunnelClient,
    create_ssl_context, create_client_ssl_context
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tunnel.log')
    ]
)
logger = logging.getLogger('Tunnel')

async def run_server(host: str, port: int, certfile: str = None, keyfile: str = None):
    """Run the tunnel server."""
    ssl_context = None
    if certfile and keyfile:
        ssl_context = create_ssl_context(certfile, keyfile)
        logger.info(f"SSL/TLS enabled with certificate: {certfile}")
    
    server = TunnelServer(host=host, port=port, ssl_context=ssl_context)
    
    try:
        await server.start()
    except asyncio.CancelledError:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        await server.stop()

async def run_client(server_url: str, local_port: int, insecure: bool = False):
    """Run the tunnel client."""
    ssl_context = None
    
    if server_url.startswith('wss://'):
        ssl_context = create_client_ssl_context()
        if insecure:
            logger.warning("Running in INSECURE MODE - SSL verification is disabled!")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    
    client = TunnelClient(
        server_uri=server_url,
        local_port=local_port,
        ssl_context=ssl_context
    )
    
    try:
        await client.run()
    except asyncio.CancelledError:
        logger.info("Client shutdown requested")
    except Exception as e:
        logger.error(f"Client error: {e}", exc_info=True)
    finally:
        await client.stop()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Run the tunnel server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=8443, help='Port to listen on')
    server_parser.add_argument('--certfile', help='Path to SSL certificate file')
    server_parser.add_argument('--keyfile', help='Path to SSL private key file')
    
    # Client command
    client_parser = subparsers.add_parser('client', help='Run the tunnel client')
    client_parser.add_argument('--server', required=True, help='WebSocket server URL (e.g., wss://example.com:8443)')
    client_parser.add_argument('--port', type=int, default=1080, help='Local port for SOCKS5 proxy')
    client_parser.add_argument('--insecure', action='store_true', help='Disable SSL certificate verification')
    
    # Both command (for testing)
    both_parser = subparsers.add_parser('both', help='Run both client and server (for testing)')
    both_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    both_parser.add_argument('--port', type=int, default=8443, help='Port to listen on')
    both_parser.add_argument('--socks-port', type=int, default=1080, help='Local port for SOCKS5 proxy')
    both_parser.add_argument('--certfile', default='certs/cert.pem', help='Path to SSL certificate file')
    both_parser.add_argument('--keyfile', default='certs/key.pem', help='Path to SSL private key file')
    
    args = parser.parse_args()
    
    if args.command == 'server':
        await run_server(args.host, args.port, args.certfile, args.keyfile)
    elif args.command == 'client':
        await run_client(args.server, args.port, args.insecure)
    elif args.command == 'both':
        # Generate certificates if they don't exist
        cert_path = Path(args.certfile)
        key_path = Path(args.keyfile)
        
        if not cert_path.exists() or not key_path.exists():
            logger.warning("Certificate files not found. Generating self-signed certificates...")
            import generate_certs
            await generate_certs.main()
        
        # Run both server and client
        server_task = asyncio.create_task(
            run_server(args.host, args.port, str(cert_path), str(key_path))
        )
        
        # Give the server a moment to start
        await asyncio.sleep(1)
        
        client_task = asyncio.create_task(
            run_client(
                f"wss://{args.host}:{args.port}",
                args.socks_port,
                insecure=True
            )
        )
        
        try:
            await asyncio.gather(server_task, client_task)
        except asyncio.CancelledError:
            logger.info("Shutting down...")
            server_task.cancel()
            client_task.cancel()
            await asyncio.gather(server_task, client_task, return_exceptions=True)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
