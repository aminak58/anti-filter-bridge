"""
Anti-Filter Bridge Utilities

This module provides utility functions for managing the Anti-Filter Bridge service,
including installation, uninstallation, and system service management.
"""
import argparse
import getpass
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('afb_utils.log')
    ]
)
logger = logging.getLogger('AFB_Utils')

# Platform-specific configuration
IS_WINDOWS = platform.system().lower() == 'windows'
IS_LINUX = platform.system().lower() == 'linux'
IS_MAC = platform.system().lower() == 'darwin'

# Default installation paths
if IS_WINDOWS:
    DEFAULT_INSTALL_DIR = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'AntiFilterBridge')
    CONFIG_DIR = os.path.join(os.environ.get('APPDATA', ''), 'AntiFilterBridge')
    LOG_DIR = os.path.join(CONFIG_DIR, 'logs')
    SERVICE_NAME = 'AntiFilterBridge'
    SERVICE_DISPLAY_NAME = 'Anti-Filter Bridge Service'
    SERVICE_DESCRIPTION = 'Provides secure tunneling capabilities to bypass internet restrictions.'
else:
    DEFAULT_INSTALL_DIR = '/opt/antifilterbridge'
    CONFIG_DIR = '/etc/antifilterbridge'
    LOG_DIR = '/var/log/antifilterbridge'
    SERVICE_NAME = 'antifilterbridge'
    SERVICE_DISPLAY_NAME = 'Anti-Filter Bridge Service'
    SERVICE_DESCRIPTION = 'Provides secure tunneling capabilities to bypass internet restrictions.'

# Required files for installation
REQUIRED_FILES = [
    'anti_filter_bridge/__init__.py',
    'anti_filter_bridge/server.py',
    'anti_filter_bridge/client.py',
    'anti_filter_bridge/cli.py',
    'requirements.txt',
    'README.md',
    'LICENSE'
]

# Service templates
if IS_WINDOWS:
    SERVICE_TEMPLATE = """
[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={install_dir}
ExecStart={python} -m anti_filter_bridge.cli server start --config {config_file}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
else:
    SERVICE_TEMPLATE = """
[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={install_dir}
ExecStart={python} -m anti_filter_bridge.cli server start --config {config_file}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

class AFBInstaller:
    """A class to handle the installation and management of the Anti-Filter Bridge service."""
    
    def __init__(self, install_dir: str = None, config_dir: str = None, log_dir: str = None):
        """Initialize the installer.
        
        Args:
            install_dir: Directory to install the service to
            config_dir: Directory for configuration files
            log_dir: Directory for log files
        """
        self.install_dir = Path(install_dir) if install_dir else Path(DEFAULT_INSTALL_DIR)
        self.config_dir = Path(config_dir) if config_dir else Path(CONFIG_DIR)
        self.log_dir = Path(log_dir) if log_dir else Path(LOG_DIR)
        self.python = sys.executable
        self.service_file = None
        
        # Set up service file path based on platform
        if IS_WINDOWS:
            self.service_file = f"{SERVICE_NAME}.exe"
        elif IS_LINUX:
            self.service_file = f"/etc/systemd/system/{SERVICE_NAME}.service"
        elif IS_MAC:
            self.service_file = f"/Library/LaunchDaemons/org.antifilterbridge.{SERVICE_NAME}.plist"
    
    def check_requirements(self) -> Tuple[bool, List[str]]:
        """Check if all requirements are met for installation.
        
        Returns:
            Tuple of (success, messages)
        """
        messages = []
        success = True
        
        # Check Python version
        if sys.version_info < (3, 8):
            messages.append("Python 3.8 or higher is required")
            success = False
        
        # Check if running as root/administrator
        if not IS_WINDOWS and os.geteuid() != 0:
            messages.append("Root/administrator privileges are required for installation")
            success = False
        
        # Check if required files exist
        for file in REQUIRED_FILES:
            if not os.path.exists(file):
                messages.append(f"Required file not found: {file}")
                success = False
        
        return success, messages
    
    def create_directories(self) -> bool:
        """Create necessary directories.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log directory
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set permissions (Unix-like systems)
            if not IS_WINDOWS:
                os.chmod(self.install_dir, 0o755)
                os.chmod(self.config_dir, 0o755)
                os.chmod(self.log_dir, 0o755)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False
    
    def copy_files(self) -> bool:
        """Copy required files to the installation directory.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Copy package directory
            if os.path.exists('anti_filter_bridge'):
                dest_dir = self.install_dir / 'anti_filter_bridge'
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree('anti_filter_bridge', dest_dir)
            
            # Copy individual files
            for file in ['requirements.txt', 'README.md', 'LICENSE']:
                if os.path.exists(file):
                    shutil.copy2(file, self.install_dir / file)
            
            # Create a default config file if it doesn't exist
            config_file = self.config_dir / 'config.ini'
            if not config_file.exists():
                with open(config_file, 'w') as f:
                    f.write("# Anti-Filter Bridge Configuration\n\n[server]\nhost = 0.0.0.0\nport = 8443\n\n[client]\nserver_url = wss://your-server:8443\nlocal_port = 1080\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy files: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Install dependencies using pip
            requirements_file = self.install_dir / 'requirements.txt'
            if requirements_file.exists():
                subprocess.check_call([
                    self.python, '-m', 'pip', 'install', '--upgrade', 'pip'
                ])
                subprocess.check_call([
                    self.python, '-m', 'pip', 'install', '-r', str(requirements_file)
                ])
                return True
            else:
                logger.error(f"Requirements file not found: {requirements_file}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def create_service(self) -> bool:
        """Create a system service for the bridge.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if IS_WINDOWS:
                return self._create_windows_service()
            elif IS_LINUX:
                return self._create_linux_service()
            elif IS_MAC:
                return self._create_mac_service()
            else:
                logger.error("Unsupported operating system")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create service: {e}")
            return False
    
    def _create_windows_service(self) -> bool:
        """Create a Windows service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Install NSSM (Non-Sucking Service Manager) if not installed
            nssm_path = shutil.which('nssm')
            if not nssm_path:
                logger.info("NSSM not found. Installing NSSM...")
                nssm_url = "https://nssm.cc/release/nssm-2.24.zip"
                nssm_zip = "nssm.zip"
                nssm_dir = "nssm"
                
                # Download and extract NSSM
                import urllib.request
                import zipfile
                
                urllib.request.urlretrieve(nssm_url, nssm_zip)
                with zipfile.ZipFile(nssm_zip, 'r') as zip_ref:
                    zip_ref.extractall(nssm_dir)
                
                # Copy NSSM to system32
                if platform.machine().endswith('64'):
                    nssm_exe = os.path.join(nssm_dir, 'nssm-2.24', 'win64', 'nssm.exe')
                else:
                    nssm_exe = os.path.join(nssm_dir, 'nssm-2.24', 'win32', 'nssm.exe')
                
                shutil.copy2(nssm_exe, 'C:\\Windows\\System32\\nssm.exe')
                os.remove(nssm_zip)
                shutil.rmtree(nssm_dir)
                nssm_path = 'nssm.exe'
            
            # Create the service
            service_path = os.path.join(self.install_dir, 'anti_filter_bridge', 'cli.py')
            
            # Remove the service if it already exists
            subprocess.run([nssm_path, 'remove', SERVICE_NAME, 'confirm'], 
                         stderr=subprocess.DEVNULL, 
                         stdout=subprocess.DEVNULL)
            
            # Install the service
            subprocess.check_call([
                nssm_path, 'install', SERVICE_NAME, 
                self.python, service_path, 'server', 'start',
                '--config', str(self.config_dir / 'config.ini')
            ])
            
            # Set service description
            subprocess.check_call([
                nssm_path, 'set', SERVICE_NAME, 'Description',
                f'"{SERVICE_DESCRIPTION}"'
            ])
            
            # Set service display name
            subprocess.check_call([
                nssm_path, 'set', SERVICE_NAME, 'DisplayName',
                f'"{SERVICE_DISPLAY_NAME}"'
            ])
            
            # Set working directory
            subprocess.check_call([
                nssm_path, 'set', SERVICE_NAME, 'AppDirectory',
                str(self.install_dir)
            ])
            
            # Set startup type to automatic
            subprocess.check_call([
                'sc', 'config', SERVICE_NAME, 'start=', 'auto'
            ])
            
            logger.info(f"Windows service '{SERVICE_NAME}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Windows service: {e}")
            return False
    
    def _create_linux_service(self) -> bool:
        """Create a Linux systemd service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the service file
            service_content = SERVICE_TEMPLATE.format(
                description=SERVICE_DESCRIPTION,
                user=getpass.getuser(),
                install_dir=self.install_dir,
                python=self.python,
                config_file=str(self.config_dir / 'config.ini')
            )
            
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            
            # Set permissions
            os.chmod(self.service_file, 0o644)
            
            # Reload systemd
            subprocess.check_call(['systemctl', 'daemon-reload'])
            
            # Enable the service
            subprocess.check_call(['systemctl', 'enable', SERVICE_NAME])
            
            logger.info(f"Linux service '{SERVICE_NAME}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Linux service: {e}")
            return False
    
    def _create_mac_service(self) -> bool:
        """Create a macOS launchd service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the plist file
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>org.antifilterbridge.{SERVICE_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{self.python}</string>
        <string>-m</string>
        <string>anti_filter_bridge.cli</string>
        <string>server</string>
        <string>start</string>
        <string>--config</string>
        <string>{self.config_dir / 'config.ini'}</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{self.install_dir}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>{self.log_dir}/service.log</string>
    
    <key>StandardErrorPath</key>
    <string>{self.log_dir}/service.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
"""
            with open(self.service_file, 'w') as f:
                f.write(plist_content)
            
            # Set permissions
            os.chmod(self.service_file, 0o644)
            
            # Load the service
            subprocess.check_call(['launchctl', 'load', '-w', self.service_file])
            
            logger.info(f"macOS service '{SERVICE_NAME}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create macOS service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if IS_WINDOWS:
                subprocess.check_call(['net', 'start', SERVICE_NAME])
            elif IS_LINUX:
                subprocess.check_call(['systemctl', 'start', SERVICE_NAME])
            elif IS_MAC:
                subprocess.check_call(['launchctl', 'start', f'org.antifilterbridge.{SERVICE_NAME}'])
            
            logger.info(f"Service '{SERVICE_NAME}' started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if IS_WINDOWS:
                subprocess.check_call(['net', 'stop', SERVICE_NAME])
            elif IS_LINUX:
                subprocess.check_call(['systemctl', 'stop', SERVICE_NAME])
            elif IS_MAC:
                subprocess.check_call(['launchctl', 'stop', f'org.antifilterbridge.{SERVICE_NAME}'])
            
            logger.info(f"Service '{SERVICE_NAME}' stopped successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Stop the service first
            self.stop_service()
            
            if IS_WINDOWS:
                # Remove the service using NSSM
                nssm_path = shutil.which('nssm') or 'nssm.exe'
                subprocess.run([nssm_path, 'remove', SERVICE_NAME, 'confirm'], 
                             stderr=subprocess.DEVNULL, 
                             stdout=subprocess.DEVNULL)
                
            elif IS_LINUX:
                # Disable and remove the service file
                subprocess.run(['systemctl', 'disable', SERVICE_NAME], 
                             stderr=subprocess.DEVNULL)
                if os.path.exists(self.service_file):
                    os.remove(self.service_file)
                subprocess.check_call(['systemctl', 'daemon-reload'])
                
            elif IS_MAC:
                # Unload and remove the plist file
                subprocess.run(['launchctl', 'unload', self.service_file],
                             stderr=subprocess.DEVNULL)
                if os.path.exists(self.service_file):
                    os.remove(self.service_file)
            
            logger.info(f"Service '{SERVICE_NAME}' uninstalled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall service: {e}")
            return False
    
    def install(self) -> bool:
        """Run the installation process.
        
        Returns:
            bool: True if installation was successful, False otherwise
        """
        logger.info("Starting Anti-Filter Bridge installation...")
        
        # Check requirements
        logger.info("Checking requirements...")
        success, messages = self.check_requirements()
        if not success:
            for msg in messages:
                logger.error(msg)
            return False
        
        # Create directories
        logger.info("Creating directories...")
        if not self.create_directories():
            return False
        
        # Copy files
        logger.info("Copying files...")
        if not self.copy_files():
            return False
        
        # Install dependencies
        logger.info("Installing dependencies...")
        if not self.install_dependencies():
            return False
        
        # Create service
        logger.info("Creating service...")
        if not self.create_service():
            return False
        
        # Start service
        logger.info("Starting service...")
        if not self.start_service():
            return False
        
        logger.info("\nInstallation completed successfully!")
        logger.info(f"Installation directory: {self.install_dir}")
        logger.info(f"Configuration directory: {self.config_dir}")
        logger.info(f"Log directory: {self.log_dir}")
        logger.info("\nYou can now use the Anti-Filter Bridge service.")
        
        return True
    
    def uninstall(self) -> bool:
        """Uninstall the Anti-Filter Bridge.
        
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        logger.info("Starting Anti-Filter Bridge uninstallation...")
        
        # Uninstall service
        logger.info("Uninstalling service...")
        self.uninstall_service()
        
        # Remove installation directory
        logger.info("Removing installation directory...")
        if os.path.exists(self.install_dir):
            try:
                shutil.rmtree(self.install_dir)
            except Exception as e:
                logger.error(f"Failed to remove installation directory: {e}")
        
        # Remove configuration directory (but keep logs)
        logger.info("Removing configuration directory...")
        if os.path.exists(self.config_dir):
            try:
                shutil.rmtree(self.config_dir)
            except Exception as e:
                logger.error(f"Failed to remove configuration directory: {e}")
        
        logger.info("\nUninstallation completed!")
        logger.info("Note: Log files were kept in the log directory.")
        
        return True

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge Installer')
    
    # Main commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install Anti-Filter Bridge')
    install_parser.add_argument('--install-dir', help='Installation directory')
    install_parser.add_argument('--config-dir', help='Configuration directory')
    install_parser.add_argument('--log-dir', help='Log directory')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall Anti-Filter Bridge')
    uninstall_parser.add_argument('--install-dir', help='Installation directory')
    uninstall_parser.add_argument('--config-dir', help='Configuration directory')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the service')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop the service')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart the service')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check service status')
    
    return parser.parse_args()

def main():
    """Main entry point for the installer."""
    args = parse_arguments()
    
    # Create installer instance
    installer = AFBInstaller(
        install_dir=args.install_dir if hasattr(args, 'install_dir') and args.install_dir else None,
        config_dir=args.config_dir if hasattr(args, 'config_dir') and args.config_dir else None,
        log_dir=args.log_dir if hasattr(args, 'log_dir') and args.log_dir else None
    )
    
    # Execute the requested command
    if args.command == 'install':
        return 0 if installer.install() else 1
    elif args.command == 'uninstall':
        return 0 if installer.uninstall() else 1
    elif args.command == 'start':
        return 0 if installer.start_service() else 1
    elif args.command == 'stop':
        return 0 if installer.stop_service() else 1
    elif args.command == 'restart':
        return (0 if installer.stop_service() and installer.start_service() else 1)
    elif args.command == 'status':
        # This is a simplified status check
        try:
            if IS_WINDOWS:
                output = subprocess.check_output(['sc', 'query', SERVICE_NAME])
                print(output.decode('utf-8', 'ignore'))
            elif IS_LINUX:
                subprocess.check_call(['systemctl', 'status', SERVICE_NAME])
            elif IS_MAC:
                subprocess.check_call(['launchctl', 'list', f'org.antifilterbridge.{SERVICE_NAME}'])
            return 0
        except subprocess.CalledProcessError:
            print("Service is not running or not installed.")
            return 1
    else:
        print("No command specified. Use --help for usage information.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)
