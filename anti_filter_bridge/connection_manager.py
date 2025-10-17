"""
Connection management for handling weak connections and long-term stability.
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Set, Tuple
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger('ConnectionManager')

class ConnectionManager:
    """Manages WebSocket connections with optimizations for weak networks."""
    
    def __init__(self, 
                 initial_timeout: float = 10.0,
                 max_timeout: float = 300.0,
                 backoff_factor: float = 1.5,
                 max_retries: int = 5,
                 ping_interval: float = 30.0,
                 max_message_size: int = 10 * 1024 * 1024):
        """
        Initialize the connection manager.
        
        Args:
            initial_timeout: Initial connection timeout in seconds
            max_timeout: Maximum connection timeout in seconds
            backoff_factor: Multiplier for exponential backoff
            max_retries: Maximum number of retry attempts
            ping_interval: Interval for keep-alive pings in seconds
            max_message_size: Maximum message size in bytes
        """
        self.initial_timeout = initial_timeout
        self.max_timeout = max_timeout
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries
        self.ping_interval = ping_interval
        self.max_message_size = max_message_size
        self.connections: Dict[WebSocketServerProtocol, Dict] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new WebSocket connection with improved reliability."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New connection from {client_id}")
        
        # Initialize connection state
        self.connections[websocket] = {
            'id': client_id,
            'connected_at': time.time(),
            'last_activity': time.time(),
            'retry_count': 0,
            'timeout': self.initial_timeout,
            'active': True
        }
        
        try:
            # Set up ping/pong for connection health
            websocket.ping_interval = self.ping_interval
            
            async for message in websocket:
                # Update last activity timestamp
                self.connections[websocket]['last_activity'] = time.time()
                
                # Process the message (echo for now, will be replaced with actual processing)
                await self._process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connection closed by {client_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling connection {client_id}: {e}", exc_info=True)
        finally:
            await self._cleanup_connection(websocket)
    
    async def _process_message(self, websocket: WebSocketServerProtocol, message: bytes):
        """Process incoming WebSocket messages with error handling."""
        try:
            # Echo the message back for now
            # In a real implementation, this would route the traffic
            await websocket.send(message)
            
        except websockets.exceptions.ConnectionClosed:
            raise  # Let the outer handler deal with this
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Optionally implement retry logic here
    
    async def _cleanup_connection(self, websocket: WebSocketServerProtocol):
        """Clean up connection resources."""
        if websocket in self.connections:
            conn_info = self.connections.pop(websocket)
            logger.info(f"Connection {conn_info['id']} cleaned up")
            
        try:
            await websocket.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
    
    async def monitor_connections(self):
        """Monitor connections for timeouts and health."""
        self._running = True
        
        while self._running:
            try:
                current_time = time.time()
                dead_connections = []
                
                # Check each connection
                for websocket, conn_info in list(self.connections.items()):
                    if not conn_info['active']:
                        continue
                        
                    # Check for connection timeout
                    time_since_activity = current_time - conn_info['last_activity']
                    if time_since_activity > self.ping_interval * 3:  # Allow some grace period
                        logger.warning(f"Connection {conn_info['id']} timed out")
                        dead_connections.append(websocket)
                        continue
                    
                    # Implement adaptive timeout based on connection quality
                    if conn_info['retry_count'] > 0:
                        # Gradually increase timeout for unstable connections
                        new_timeout = min(
                            self.initial_timeout * (self.backoff_factor ** conn_info['retry_count']),
                            self.max_timeout
                        )
                        conn_info['timeout'] = new_timeout
                
                # Clean up dead connections
                for websocket in dead_connections:
                    await self._cleanup_connection(websocket)
                
                # Sleep before next check
                await asyncio.sleep(min(5.0, self.ping_interval / 2))
                
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}", exc_info=True)
                await asyncio.sleep(5)  # Prevent tight loop on errors
    
    async def start_monitoring(self):
        """Start the connection monitoring task."""
        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self.monitor_connections())
    
    async def stop_monitoring(self):
        """Stop the connection monitoring task."""
        self._running = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def close_all(self):
        """Close all managed connections and stop monitoring."""
        await self.stop_monitoring()
        
        # Close all connections
        tasks = [self._cleanup_connection(ws) for ws in list(self.connections.keys())]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.connections.clear()

# Singleton instance
connection_manager = ConnectionManager()
