"""
Command Line Interface for Anti-Filter Bridge Client
"""
import click
import asyncio
import logging
import sys
import os
import ssl
from typing import Optional
from client import TunnelClient, create_client_ssl_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tunnel_client.log')
    ]
)
logger = logging.getLogger('TunnelCLI')

@click.group()
def cli():
    """Anti-Filter Bridge - Secure Tunnel Client"""
    pass

@cli.command()
@click.option('--server', '-s', 
              default='wss://your-server-address:8443', 
              help='WebSocket server URL (e.g., wss://example.com:8443)')
@click.option('--local-port', '-p', 
              default=1080, 
              help='Local port to listen on (default: 1080)')
@click.option('--insecure/--secure', 
              default=False, 
              help='Skip SSL certificate verification (not recommended)')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
              default='INFO', 
              help='Set the logging level')
def start(server: str, local_port: int, insecure: bool, log_level: str):
    """Start the tunnel client"""
    # Set log level
    logger.setLevel(log_level)
    
    # Create SSL context
    ssl_context = None
    if server.startswith('wss://'):
        ssl_context = create_client_ssl_context()
        if insecure:
            logger.warning("⚠️  Running in INSECURE MODE - SSL certificate verification is disabled!")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    
    # Create and run client
    client = TunnelClient(
        server_uri=server,
        local_port=local_port,
        ssl_context=ssl_context
    )
    
    try:
        logger.info(f"🚀 Starting Anti-Filter Bridge Client")
        logger.info(f"🔗 Server: {server}")
        logger.info(f"🏠 Local SOCKS5 Proxy: 127.0.0.1:{local_port}")
        logger.info(f"🔒 SSL Verification: {'enabled' not in insecure}")
        logger.info("🔄 Press Ctrl+C to stop")
        
        # Run the client
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("\n🛑 Received stop signal. Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("👋 Tunnel client stopped")

@cli.command()
def version():
    """Show version information"""
    click.echo("Anti-Filter Bridge Client v0.1.0")
    click.echo("A secure tunnel to bypass internet restrictions")
    click.echo("https://github.com/yourusername/anti-filter-bridge")

if __name__ == '__main__':
    cli()
