"""
WebSocket tunnel client for the Anti-Filter Bridge.
Creates a local SOCKS proxy that tunnels traffic through a WebSocket connection.
"""
import asyncio
import websockets
import websockets.exceptions
import logging
import json
import socket
import ssl
import struct
import signal
import sys
from typing import Optional, Dict, Any, Tuple, cast, Callable, Awaitable

# Configure logger (will be configured by CLI)
logger = logging.getLogger('TunnelClient')

class TunnelClient:
    def __init__(self, server_uri: str = "ws://localhost:8081", local_port: int = 1080, ssl_context=None):
        self.server_uri = server_uri
        self.local_port = local_port
        self.ssl_context = ssl_context
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.server: Optional[asyncio.Server] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

    async def connect_to_server(self) -> bool:
        """Establish WebSocket connection to the tunnel server"""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"🔗 Attempting to connect to {self.server_uri}... (Attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                self.websocket = await websockets.connect(
                    self.server_uri,
                    ssl=self.ssl_context,
                    ping_interval=30,
                    ping_timeout=30,
                    close_timeout=1,
                    max_size=10 * 1024 * 1024  # 10MB max message size
                )
                logger.info(f"✅ Connected to tunnel server at {self.server_uri}")
                self.reconnect_attempts = 0  # Reset reconnect attempts on success
                return True
            except websockets.exceptions.InvalidURI as e:
                logger.error(f"❌ Invalid server URI: {e}")
                break
            except websockets.exceptions.InvalidHandshake as e:
                logger.error(f"❌ Handshake failed: {e}")
                break
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                self.reconnect_attempts += 1
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error("❌ Max reconnection attempts reached. Giving up.")
                    break
                logger.warning(f"⚠️  Connection failed. Retrying in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"❌ Failed to connect to tunnel server: {e}", exc_info=True)
                break
        
        return False

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle incoming SOCKS5 client connections"""
        client_addr = writer.get_extra_info('peername')
        logger.debug(f"New connection from {client_addr}")
        try:
            # SOCKS5 handshake
            await self._socks5_handshake(reader, writer)
            
            # Get target address
            target_host, target_port = await self._get_target_address(reader, writer)
            
            # Check if WebSocket is connected
            if not self.websocket:
                logger.error("WebSocket connection is not initialized")
                writer.close()
                await writer.wait_closed()
                return
                
            try:
                # Check if WebSocket is closed
                if hasattr(self.websocket, 'closed') and self.websocket.closed:
                    logger.error("WebSocket connection is closed")
                    writer.close()
                    await writer.wait_closed()
                    return
                    
                # Forward data between client and tunnel
                if self.websocket is not None:
                    await self.traffic_through_tunnel(reader, writer, self.websocket, target_host, target_port)
                else:
                    logger.error("No WebSocket connection available")
                    writer.close()
                    await writer.wait_closed()
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                writer.close()
                await writer.wait_closed()
                return
            except Exception as e:
                logger.error(f"Error in traffic through tunnel: {e}", exc_info=True)
                writer.close()
                await writer.wait_closed()
                return
                
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {str(e)}")
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
        except asyncio.CancelledError:
            logger.info(f"Connection cancelled for {client_addr}")
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
        except Exception as e:
            logger.error(f"Unexpected error handling client {client_addr}: {str(e)}")
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            logger.debug(f"Connection closed for {client_addr}")

    async def _socks5_handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Perform SOCKS5 handshake"""
        # Read client auth methods
        data = await reader.read(2)
        if len(data) < 2:
            raise Exception("Invalid SOCKS5 handshake: insufficient data")
            
        ver, n_methods = data
        if ver != 0x05:  # SOCKS5
            raise Exception(f"Unsupported SOCKS version: {ver}")
            
        # Read the methods
        methods = await reader.read(n_methods)
        if len(methods) != n_methods:
            raise Exception("Invalid SOCKS5 handshake: methods length mismatch")
        
        # We only support no-auth (0x00)
        if 0x00 not in methods:
            writer.write(bytes([0x05, 0xFF]))  # No acceptable methods
            await writer.drain()
            raise Exception("No supported auth methods")
            
        # Send selected auth method (no-auth)
        writer.write(bytes([0x05, 0x00]))
        await writer.drain()

    async def _get_target_address(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> tuple:
        """Get target address from SOCKS5 request"""
        # Read request
        version, cmd, _, addr_type = await reader.read(4)
        
        if version != 0x05 or cmd != 0x01:  # Only support CONNECT command
            writer.write(bytes([0x05, 0x07, 0x00, 0x01, 0, 0, 0, 0, 0, 0]))  # Command not supported
            await writer.drain()
            return None, None
            
        # Get target address
        if addr_type == 0x01:  # IPv4
            addr = await reader.read(4)
            target_host = socket.inet_ntop(socket.AF_INET, addr)
        elif addr_type == 0x03:  # Domain name
            addr_len = int.from_bytes(await reader.read(1), 'big')
            target_host = (await reader.read(addr_len)).decode('ascii')
        elif addr_type == 0x04:  # IPv6
            addr = await reader.read(16)
            target_host = socket.inet_ntop(socket.AF_INET6, addr)
        else:
            writer.write(bytes([0x05, 0x08, 0x00, 0x01, 0, 0, 0, 0, 0, 0]))  # Address type not supported
            await writer.drain()
            return None, None
            
        # Get target port
        target_port = int.from_bytes(await reader.read(2), 'big')
        
        # Send success response
        writer.write(bytes([0x05, 0x00, 0x00, 0x01, 0, 0, 0, 0, 0, 0]))
        await writer.drain()
        
        return target_host, target_port

    async def traffic_through_tunnel(self, reader: asyncio.StreamReader, 
                                   writer: asyncio.StreamWriter,
                                   websocket: websockets.WebSocketClientProtocol,
                                   target_host: str, target_port: int) -> None:
        """Forward traffic through WebSocket tunnel
        
        Args:
            reader: StreamReader for reading data from the client
            writer: StreamWriter for writing data back to the client
            websocket: WebSocket connection to the tunnel server
            target_host: Target host to connect to
            target_port: Target port to connect to
        """
        try:
            logger.info(f"Starting tunnel to {target_host}:{target_port}")
            
            while True:
                # Read data from client
                data = await reader.read(4096)
                if not data:
                    logger.debug("No more data from client, closing tunnel")
                    break
                
                logger.debug(f"Sending {len(data)} bytes to tunnel")
                
                # Forward data through WebSocket
                await websocket.send(json.dumps({
                    'type': 'data',
                    'target_host': target_host,
                    'target_port': target_port,
                    'data': data.hex()
                }))
                
                # Get response from tunnel
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    
                    if response_data.get('type') == 'data':
                        # Forward response back to client
                        response_bytes = bytes.fromhex(response_data['data'])
                        logger.debug(f"Received {len(response_bytes)} bytes from tunnel")
                        writer.write(response_bytes)
                        await writer.drain()
                    elif response_data.get('type') == 'error':
                        logger.error(f"Tunnel error: {response_data.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for response from tunnel")
                    break
                except websockets.exceptions.ConnectionClosed as e:
                    logger.error(f"WebSocket connection closed: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in tunnel: {e}", exc_info=True)
        finally:
            logger.info(f"Closing tunnel to {target_host}:{target_port}")
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    async def start(self) -> None:
        """Start the SOCKS5 proxy server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                '0.0.0.0',
                self.local_port,
                reuse_address=True,
                reuse_port=True
            )
            
            # Get the actual port if using port 0 (random port)
            if self.local_port == 0:
                self.local_port = self.server.sockets[0].getsockname()[1]
                
            logger.info(f"🚀 SOCKS5 proxy started on 0.0.0.0:{self.local_port}")
            logger.info(f"🔄 Connecting to tunnel server at {self.server_uri}...")
            
            # Connect to the WebSocket server
            if not await self.connect_to_server():
                logger.error("❌ Failed to connect to tunnel server. Exiting...")
                await self.stop()
                return
                
            # Start a keepalive task
            self.keepalive_task = asyncio.create_task(self.keepalive())
            
            # Keep the connection alive
            try:
                async with self.server:
                    await self.server.serve_forever()
            except asyncio.CancelledError:
                logger.info("\n👋 Shutting down...")
            except Exception as e:
                logger.error(f"❌ Error in server: {e}", exc_info=True)
            finally:
                await self.stop()
                
        except OSError as e:
            logger.error(f"❌ Failed to start SOCKS5 proxy: {e}")
            if e.errno == 10048:  # Address already in use
                logger.error(f"Port {self.local_port} is already in use. Please choose a different port.")
            raise
            
    async def keepalive(self):
        """Send periodic pings to keep the connection alive"""
        while self.running and self.websocket and not self.websocket.closed:
            try:
                await asyncio.sleep(25)  # Send ping every 25 seconds (less than the 30s timeout)
                if self.websocket and not self.websocket.closed:
                    await self.websocket.ping()
            except Exception as e:
                logger.warning(f"⚠️  Keepalive ping failed: {e}")
                if not await self.reconnect():
                    break

    async def stop(self) -> None:
        """Stop the tunnel client"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.websocket:
            await self.websocket.close()
        logger.info("Tunnel client stopped")

def create_client_ssl_context() -> ssl.SSLContext:
    """
    Create an SSL context for the client (for WSS)
    
    Returns:
        ssl.SSLContext: Configured SSL context
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    # Add system trusted CA certificates
    ssl_context.load_default_certs()
    
    # Set minimum TLS version (TLS 1.2 or higher)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    
    # Set preferred ciphers
    ssl_context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305')
    
    return ssl_context

def main():
    """Main function to run the tunnel client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge Client')
    parser.add_argument('--server', default='ws://localhost:8081', help='WebSocket server URL')
    parser.add_argument('--local-port', type=int, default=1080, help='Local SOCKS5 port')
    parser.add_argument('--insecure', action='store_true', help='Skip SSL verification')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create SSL context
    ssl_context = None
    if args.server.startswith('wss://'):
        ssl_context = create_client_ssl_context()
        if args.insecure:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    
    # Create and run client
    client = TunnelClient(
        server_uri=args.server,
        local_port=args.local_port,
        ssl_context=ssl_context
    )
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        try:
            loop.run_until_complete(client.stop())
            loop.close()
        except:
            pass

async def run(self):
    """
    Run the tunnel client with error handling and reconnection logic
    
    This method manages the client's lifecycle, including reconnection attempts
    and proper resource cleanup.
    """
    self.running = True
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
    
    try:
        while self.running:
            try:
                if not await self.connect_to_server():
                    logger.error("Failed to connect to server. Retrying...")
                    await asyncio.sleep(5)
                    continue
                
                # Start the SOCKS5 server
                self.server = await asyncio.start_server(
                    self.handle_client,
                    '127.0.0.1',
                    self.local_port,
                    reuse_port=True
                )
                
                addr = self.server.sockets[0].getsockname()
                logger.info(f"✅ SOCKS5 proxy server started on {addr[0]}:{addr[1]}")
                
                # Keep the connection alive
                while self.running and self.websocket and not self.websocket.closed:
                    await asyncio.sleep(1)
                
            except (websockets.exceptions.ConnectionClosed, ConnectionError) as e:
                logger.warning(f"Connection lost: {e}. Reconnecting...")
                await self._reconnect()
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Prevent tight loop on repeated errors
    
    except asyncio.CancelledError:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await self.stop()

async def _reconnect(self):
    """Handle reconnection logic"""
    self.reconnect_attempts += 1
    if self.reconnect_attempts > self.max_reconnect_attempts:
        logger.error("Max reconnection attempts reached. Give up.")
        self.running = False
        return
    
    delay = min(5 * self.reconnect_attempts, 60)  # Exponential backoff with max 60s
    logger.info(f"Reconnecting in {delay} seconds... (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
    await asyncio.sleep(delay)
