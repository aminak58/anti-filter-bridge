"""
WebSocket tunnel server for the Anti-Filter Bridge.
Handles incoming WebSocket connections and routes traffic between clients and targets.
"""
import asyncio
import logging
import os
import ssl
import signal
import sys
from typing import Optional, Set, Any
import websockets
from websockets.server import WebSocketServerProtocol
from aiohttp import web

try:
    from .connection_manager import connection_manager as conn_manager
except ImportError:
    # Fallback for when running as script
    from connection_manager import connection_manager as conn_manager

logger = logging.getLogger('TunnelServer')


class TunnelServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8443,
                 ssl_context: Optional[ssl.SSLContext] = None):
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.clients: Set[WebSocketServerProtocol] = set()
        self.running = False
        self.server: Optional[asyncio.Server] = None
        self.conn_manager = conn_manager
        self.http_app = None
        self.http_runner = None
        self._setup_http_app()

    def _setup_http_app(self):
        """Setup HTTP app for health checks and WebSocket"""
        self.http_app = web.Application()
        
        # Health check endpoint
        self.http_app.router.add_get('/status', self._health_check)
        self.http_app.router.add_get('/', self._root_handler)
        
        # WebSocket endpoint
        self.http_app.router.add_get('/ws', self._websocket_handler)
        
    async def _health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'message': 'Anti-Filter Bridge Server is running',
            'version': '0.1.0',
            'connections': len(self.clients)
        })
    
    async def _root_handler(self, request):
        """Root endpoint"""
        return web.json_response({
            'message': 'Anti-Filter Bridge Server',
            'status': 'running',
            'version': '0.1.0',
            'websocket_endpoint': f'wss://{self.host}:{self.port}/ws'
        })
    
    async def _websocket_handler(self, request):
        """WebSocket handler for aiohttp"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Convert to websockets format for compatibility
        class WebSocketAdapter:
            def __init__(self, ws):
                self.ws = ws
                self.remote_address = (request.remote, 0)
                self.open = True
                self.closed = False
                self._message_queue = asyncio.Queue()
                self._receive_task = None
                
                # Start message receiving task
                self._receive_task = asyncio.create_task(self._receive_loop())
            
            async def _receive_loop(self):
                """Background task to receive messages"""
                try:
                    while self.open and not self.closed:
                        try:
                            msg = await self.ws.receive()
                            if msg.type == web.WSMsgType.TEXT:
                                await self._message_queue.put(msg.data)
                            elif msg.type == web.WSMsgType.ERROR:
                                self.closed = True
                                await self._message_queue.put(websockets.exceptions.ConnectionClosed(1006, "WebSocket error"))
                                break
                            elif msg.type == web.WSMsgType.CLOSE:
                                self.closed = True
                                await self._message_queue.put(websockets.exceptions.ConnectionClosed(1000, "WebSocket closed"))
                                break
                            else:
                                self.closed = True
                                await self._message_queue.put(websockets.exceptions.ConnectionClosed(1000, "WebSocket closed"))
                                break
                        except Exception as e:
                            self.closed = True
                            await self._message_queue.put(websockets.exceptions.ConnectionClosed(1006, f"WebSocket error: {e}"))
                            break
                except Exception as e:
                    self.closed = True
                    await self._message_queue.put(websockets.exceptions.ConnectionClosed(1006, f"WebSocket error: {e}"))
            
            async def send(self, data):
                if self.open and not self.closed:
                    await self.ws.send_str(data)
            
            async def recv(self):
                if self.closed:
                    raise websockets.exceptions.ConnectionClosed(1000, "WebSocket closed")
                
                try:
                    message = await self._message_queue.get()
                    if isinstance(message, Exception):
                        raise message
                    return message
                except Exception as e:
                    self.closed = True
                    raise e
            
            async def close(self):
                if not self.closed:
                    self.closed = True
                    if self._receive_task:
                        self._receive_task.cancel()
                    await self.ws.close()
                    self.open = False
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                try:
                    return await self.recv()
                except websockets.exceptions.ConnectionClosed:
                    raise StopAsyncIteration
        
        # Use the adapter
        adapter = WebSocketAdapter(ws)
        
        # Add to clients set
        self.clients.add(adapter)
        
        try:
            # Handle the client connection
            await self.handle_client(adapter, '/ws')
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
        finally:
            # Remove from clients set
            self.clients.discard(adapter)
            if adapter in self.conn_manager.connections:
                await self.conn_manager._cleanup_connection(adapter)
        
        return ws

    async def _process_request(self, path, request_headers):
        """Process HTTP requests for health checks"""
        if path == '/status':
            return web.Response(
                text='{"status":"healthy","message":"Anti-Filter Bridge Server is running","version":"0.1.0","connections":0}',
                content_type='application/json'
            )
        elif path == '/':
            return web.Response(
                text='{"message":"Anti-Filter Bridge Server","status":"running","version":"0.1.0"}',
                content_type='application/json'
            )
        return None  # Let WebSocket handle it

    async def handle_client(self, websocket, path: str):
        """Handle a new WebSocket client connection with improved reliability."""
        # Delegate connection handling to the connection manager
        await self.conn_manager.handle_connection(websocket, path)

        # Keep track of the client for server management
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info("New client connected: %s", client_addr)

        try:
            # Keep the connection alive and handle messages
            while websocket.open and not websocket.closed:
                try:
                    # Wait for a message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    logger.debug("Received message from %s: %s", client_addr, message)
                    
                    # Process the message through connection manager
                    # This is where the actual tunnel logic would go
                    await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    try:
                        await websocket.send('{"type": "ping"}')
                    except:
                        break
                except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError) as e:
                    logger.info("Client connection closed: %s: %s", client_addr, str(e))
                    break
                except Exception as e:
                    logger.error(
                        "Error in client connection %s: %s",
                        client_addr,
                        str(e),
                        exc_info=True
                    )
                    break
                    
        except Exception as e:
            logger.error(
                "Fatal error in client connection %s: %s",
                client_addr,
                str(e),
                exc_info=True
            )
        finally:
            logger.info("Client disconnected: %s", client_addr)

    async def start(self):
        """Start the WebSocket server with connection management."""
        logger.info("Starting WebSocket server on %s:%s", self.host, self.port)
        self.running = True

        # Set up signal handlers for graceful shutdown (Windows compatible)
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.stop())
                )
        except NotImplementedError:
            # Signal handlers not supported on this platform (Windows)
            logger.info("Signal handlers not supported on this platform")

        # Configure server with connection manager settings
        server_config = {
            'ping_interval': self.conn_manager.ping_interval,
            # Allow some buffer for ping timeout
            'ping_timeout': self.conn_manager.ping_interval * 2,
            'close_timeout': 5,  # Increased for better cleanup
            'max_size': self.conn_manager.max_message_size,
            'compression': 'deflate',  # Enable compression for better performance
            'max_queue': 32,  # Limit queue size to prevent memory issues
        }
        
        try:
            # Start the connection manager
            await self.conn_manager.start_monitoring()
            
            # Start HTTP server with WebSocket support
            self.http_runner = web.AppRunner(self.http_app)
            await self.http_runner.setup()
            http_site = web.TCPSite(self.http_runner, self.host, self.port, ssl_context=self.ssl_context)
            await http_site.start()
            logger.info("HTTP/WebSocket server started on https://%s:%s", self.host, self.port)
            logger.info("Health check: https://%s:%s/status", self.host, self.port)
            logger.info("WebSocket: wss://%s:%s/ws", self.host, self.port)
            
            # Keep running
            await asyncio.Future()  # Run forever
                
        except asyncio.CancelledError:
            logger.info("Server shutdown requested...")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the WebSocket server and close all client connections gracefully."""
        if not self.running:
            return

        logger.info("Initiating graceful server shutdown...")
        self.running = False

        try:
            # Stop HTTP server
            if self.http_runner:
                logger.info("Stopping HTTP server...")
                await self.http_runner.cleanup()

            # Notify all clients of impending shutdown
            if self.clients:
                logger.info("Notifying %d clients...", len(self.clients))
                await asyncio.gather(
                    *[
                        ws.send('SERVER_SHUTDOWN')
                        for ws in self.clients
                        if hasattr(ws, 'open') and ws.open and not ws.closed
                    ],
                    return_exceptions=True
                )
                await asyncio.sleep(1)  # Give clients time to process

            # Close all connections through the connection manager
            if hasattr(self, 'conn_manager'):
                logger.info("Closing all managed connections...")
                await self.conn_manager.close_all()

            # Close the server
            if self.server:
                logger.info("Closing server...")
                self.server.close()
                await self.server.wait_closed()

            logger.info("Server shutdown complete")

        except Exception as e:
            logger.error("Error during shutdown: %s", str(e), exc_info=True)
        finally:
            # Ensure all resources are released
            self.clients.clear()
            if hasattr(self, 'conn_manager'):
                await self.conn_manager.stop_monitoring()

def create_ssl_context(certfile: str, keyfile: str) -> ssl.SSLContext:
    """Create an SSL context for the server.

    Args:
        certfile: Path to the SSL certificate file
        keyfile: Path to the SSL private key file

    Returns:
        Configured SSL context
    """
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile, keyfile)
    
    # Security best practices
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | 
        ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ssl_context.set_ciphers(
        'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
        'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305'
    )
    
    return ssl_context

async def main():
    """Main entry point for the tunnel server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8443)), help='Port to listen on')
    parser.add_argument('--certfile', help='Path to SSL certificate file')
    parser.add_argument('--keyfile', help='Path to SSL private key file')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tunnel_server.log')
        ]
    )
    
    # Set up SSL if certificate and key are provided
    ssl_context = None
    if args.certfile and args.keyfile:
        try:
            ssl_context = create_ssl_context(args.certfile, args.keyfile)
            logger.info(f"SSL/TLS enabled with certificate: {args.certfile}")
        except Exception as e:
            logger.error(f"Failed to load SSL certificate: {e}")
            sys.exit(1)
    
    # Create and run the server
    server = TunnelServer(host=args.host, port=args.port, ssl_context=ssl_context)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
