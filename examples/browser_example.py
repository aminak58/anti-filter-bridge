"""
Browser Example for Anti-Filter Bridge.

This example shows how to use the Anti-Filter Bridge to route web browser traffic
through the secure tunnel using a SOCKS5 proxy.
"""
import asyncio
import logging
import os
import signal
import sys
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('browser_example.log')
    ]
)
logger = logging.getLogger('BrowserExample')

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

# Test URL to open in the browser (can be changed to any URL)
TEST_URL = 'https://example.com'

class BrowserTunnel:
    """A class to manage the tunnel and browser configuration."""
    
    def __init__(self, host: str, port: int, socks_port: int, cert_file: Path, key_file: Path):
        """Initialize the browser tunnel."""
        self.host = host
        self.port = port
        self.socks_port = socks_port
        self.cert_file = cert_file
        self.key_file = key_file
        
        self.server = None
        self.client = None
        self.server_task = None
        self.client_task = None
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """Start the tunnel and configure the browser."""
        logger.info("Starting Anti-Filter Bridge tunnel...")
        
        # Create SSL context for the server
        ssl_context = create_ssl_context(self.cert_file, self.key_file)
        
        # Create and start the server
        self.server = TunnelServer(
            host=self.host,
            port=self.port,
            ssl_context=ssl_context
        )
        
        # Create SSL context for the client
        client_ssl_context = create_client_ssl_context()
        client_ssl_context.check_hostname = False
        client_ssl_context.verify_mode = ssl.CERT_NONE  # For testing only
        
        # Create and start the client
        self.client = TunnelClient(
            server_uri=f"wss://{self.host}:{self.port}",
            local_port=self.socks_port,
            ssl_context=client_ssl_context
        )
        
        # Start both server and client
        self.server_task = asyncio.create_task(self.server.start())
        self.client_task = asyncio.create_task(self.client.run())
        
        # Give them time to start
        await asyncio.sleep(2)
        
        logger.info("Tunnel is running!")
        logger.info(f"  - Server: wss://{self.host}:{self.port}")
        logger.info(f"  - SOCKS5 Proxy: 127.0.0.1:{self.socks_port}")
        
        # Configure the browser to use the SOCKS5 proxy
        self._configure_browser()
        
        # Open a test URL in the browser
        webbrowser.open(TEST_URL)
        logger.info(f"Opened {TEST_URL} in your default web browser")
        logger.info("\nPress Ctrl+C to stop the tunnel...")
    
    def _configure_browser(self):
        """Configure the system to use the SOCKS5 proxy."""
        try:
            import platform
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows proxy settings
                import winreg
                
                # Set proxy settings in the Windows registry
                INTERNET_SETTINGS = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                    0, winreg.KEY_WRITE
                )
                
                # Enable proxy
                winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
                # Set SOCKS proxy
                winreg.SetValueEx(
                    INTERNET_SETTINGS, 'ProxyServer', 0, winreg.REG_SZ,
                    f'socks=127.0.0.1:{self.socks_port}'
                )
                # Apply changes
                winreg.SetValueEx(
                    INTERNET_SETTINGS, 'ProxyOverride', 0, winreg.REG_SZ,
                    '<local>;*.local;127.0.0.1;localhost'
                )
                
                # Notify applications of the change
                import ctypes
                internet_option_refresh = 37
                internet_option_settings_changed = 39
                internet_handle = ctypes.windll.Wininet.InternetOpenA
                internet_handle("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", 0, "", "", 0)
                ctypes.windll.Wininet.InternetSetOptionW(0, internet_option_refresh, 0, 0)
                ctypes.windll.Wininet.InternetSetOptionW(0, internet_option_settings_changed, 0, 0)
                
                logger.info("Configured system to use the SOCKS5 proxy")
                
            elif system == 'darwin':  # macOS
                # macOS proxy settings
                os.system(f'networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 {self.socks_port}')
                os.system('networksetup -setsocksfirewallproxystate Wi-Fi on')
                logger.info("Configured macOS to use the SOCKS5 proxy")
                
            elif system == 'linux':
                # Linux proxy settings (GNOME)
                os.system(f'gsettings set org.gnome.system.proxy mode "manual"')
                os.system(f'gsettings set org.gnome.system.proxy.socks host "127.0.0.1"')
                os.system(f'gsettings set org.gnome.system.proxy.socks port {self.socks_port}')
                logger.info("Configured Linux (GNOME) to use the SOCKS5 proxy")
                
        except Exception as e:
            logger.warning(f"Could not automatically configure browser: {e}")
            logger.info(f"Please manually configure your browser to use SOCKS5 proxy at 127.0.0.1:{self.socks_port}")
    
    async def stop(self):
        """Stop the tunnel and clean up."""
        logger.info("Stopping tunnel and cleaning up...")
        
        # Stop the client and server
        if self.client_task:
            self.client_task.cancel()
        if self.server_task:
            self.server_task.cancel()
        
        # Wait for tasks to complete
        tasks = []
        if self.client_task:
            tasks.append(self.client_task)
        if self.server_task:
            tasks.append(self.server_task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up client and server
        if self.client:
            await self.client.stop()
        if self.server:
            await self.server.stop()
        
        # Reset browser proxy settings
        self._reset_browser_settings()
        
        logger.info("Tunnel stopped and cleaned up")
    
    def _reset_browser_settings(self):
        """Reset the browser proxy settings to default."""
        try:
            import platform
            system = platform.system().lower()
            
            if system == 'windows':
                # Reset Windows proxy settings
                import winreg
                
                INTERNET_SETTINGS = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                    0, winreg.KEY_WRITE
                )
                
                # Disable proxy
                winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
                
                # Notify applications of the change
                import ctypes
                internet_option_refresh = 37
                internet_option_settings_changed = 39
                ctypes.windll.Wininet.InternetSetOptionW(0, internet_option_refresh, 0, 0)
                ctypes.windll.Wininet.InternetSetOptionW(0, internet_option_settings_changed, 0, 0)
                
            elif system == 'darwin':  # macOS
                # Reset macOS proxy settings
                os.system('networksetup -setsocksfirewallproxystate Wi-Fi off')
                
            elif system == 'linux':
                # Reset Linux proxy settings (GNOME)
                os.system('gsettings set org.gnome.system.proxy mode "none"')
                
            logger.info("Reset browser proxy settings")
            
        except Exception as e:
            logger.warning(f"Could not reset browser settings: {e}")
            logger.info("Please manually reset your browser proxy settings")

async def main():
    """Run the browser example."""
    # Check if certificate files exist
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        logger.error("Certificate files not found. Please run 'python generate_certs.py' first.")
        return 1
    
    # Create and start the tunnel
    tunnel = BrowserTunnel(HOST, PORT, SOCKS_PORT, CERT_FILE, KEY_FILE)
    
    try:
        await tunnel.start()
        
        # Keep the example running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        await tunnel.stop()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        logger.info("\nExample stopped by user")
        sys.exit(0)
