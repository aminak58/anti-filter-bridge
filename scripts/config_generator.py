"""
Configuration Generator for Anti-Filter Bridge

This script helps users generate configuration files for the Anti-Filter Bridge
with an interactive command-line interface.
"""
import argparse
import configparser
import getpass
import ipaddress
import json
import logging
import os
import random
import re
import secrets
import socket
import string
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('config_generator.log')
    ]
)
logger = logging.getLogger('ConfigGenerator')

# Default configuration
DEFAULT_CONFIG = {
    'server': {
        'host': '0.0.0.0',
        'port': '8443',
        'enable_auth': 'true',
        'auth_token': '',
        'max_connections': '100',
        'rate_limit': '1000',
        'log_level': 'INFO',
        'log_file': '/var/log/antifilterbridge/server.log',
    },
    'client': {
        'server_url': 'wss://your-server:8443',
        'local_port': '1080',
        'auth_token': '',
        'log_level': 'INFO',
        'log_file': '/var/log/antifilterbridge/client.log',
    },
    'tls': {
        'enabled': 'true',
        'cert_file': '/etc/antifilterbridge/certs/cert.pem',
        'key_file': '/etc/antifilterbridge/certs/key.pem',
        'ca_file': '',
        'verify_peer': 'true',
        'verify_hostname': 'true',
    },
    'security': {
        'allowed_ips': '',
        'blocked_ips': '',
        'enable_bruteforce_protection': 'true',
        'max_auth_attempts': '5',
        'ban_time': '3600',
    },
    'advanced': {
        'buffer_size': '8192',
        'timeout': '30',
        'keepalive': '30',
        'compression': 'true',
        'max_message_size': '10485760',
    },
}

class ConfigGenerator:
    """A class to generate configuration files for Anti-Filter Bridge."""
    
    def __init__(self, config_file: str = None):
        """Initialize the config generator.
        
        Args:
            config_file: Path to an existing config file to load (optional)
        """
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.loaded = False
        
        # Set default values
        self.reset_to_defaults()
        
        # Load existing config if provided
        if config_file and os.path.exists(config_file):
            self.load_config()
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = configparser.ConfigParser()
        
        # Convert the default config dictionary to ConfigParser format
        for section, options in DEFAULT_CONFIG.items():
            self.config[section] = options
        
        # Generate a random auth token if not set
        if not self.config['server']['auth_token']:
            self.config['server']['auth_token'] = self._generate_auth_token()
        
        # Set client auth token to match server by default
        if not self.config['client']['auth_token']:
            self.config['client']['auth_token'] = self.config['server']['auth_token']
    
    def load_config(self):
        """Load configuration from file."""
        if not self.config_file or not os.path.exists(self.config_file):
            logger.warning("Config file not found, using defaults")
            return False
        
        try:
            self.config.read(self.config_file)
            self.loaded = True
            logger.info(f"Configuration loaded from {self.config_file}")
            
            # Ensure all default sections and options exist
            self._ensure_defaults()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return False
    
    def save_config(self, output_file: str = None) -> bool:
        """Save configuration to file.
        
        Args:
            output_file: Path to save the config file (defaults to the loaded file)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not output_file and not self.config_file:
            logger.error("No output file specified")
            return False
        
        output_file = output_file or self.config_file
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            with open(output_file, 'w') as f:
                self.config.write(f)
            
            logger.info(f"Configuration saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
            return False
    
    def _ensure_defaults(self):
        """Ensure all default sections and options exist in the loaded config."""
        for section, options in DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config[section] = {}
            
            for option, default_value in options.items():
                if option not in self.config[section]:
                    self.config[section][option] = default_value
    
    def _generate_auth_token(self, length: int = 32) -> str:
        """Generate a secure random authentication token.
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            str: A URL-safe base64-encoded token
        """
        return secrets.token_urlsafe(length)
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate an IP address.
        
        Args:
            ip: IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _validate_port(self, port: Union[str, int]) -> bool:
        """Validate a port number.
        
        Args:
            port: Port number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            port = int(port)
            return 1 <= port <= 65535
        except (ValueError, TypeError):
            return False
    
    def _validate_url(self, url: str) -> bool:
        """Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Simple URL validation
        return bool(re.match(r'^wss?://[\w.-]+(?:\.[\w-]+)*(?::\d+)?(?:/.*)?$', url))
    
    def _get_input(self, prompt: str, default: str = '', 
                  validation_func=None, error_msg: str = None) -> str:
        """Get user input with validation.
        
        Args:
            prompt: Prompt to display
            default: Default value if user presses Enter
            validation_func: Function to validate the input
            error_msg: Error message to display if validation fails
            
        Returns:
            str: Validated user input
        """
        while True:
            # Display prompt with default value
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    return default
            else:
                user_input = input(f"{prompt}: ").strip()
                if not user_input:
                    print("This field is required.")
                    continue
            
            # Validate input if validation function is provided
            if validation_func and not validation_func(user_input):
                print(error_msg or "Invalid input. Please try again.")
                continue
                
            return user_input
    
    def _get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get a yes/no answer from the user.
        
        Args:
            prompt: Prompt to display
            default: Default value if user presses Enter
            
        Returns:
            bool: True for yes, False for no
        """
        while True:
            default_str = 'Y/n' if default else 'y/N'
            user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
            
            if not user_input:
                return default
            elif user_input in ('y', 'yes'):
                return True
            elif user_input in ('n', 'no'):
                return False
            else:
                print("Please enter 'y' or 'n'.")
    
    def _edit_server_settings(self):
        """Edit server settings interactively."""
        print("\n=== Server Settings ===\n")
        
        # Server host
        self.config['server']['host'] = self._get_input(
            "Server host (IP to bind to)",
            self.config['server']['host'],
            self._validate_ip,
            "Invalid IP address"
        )
        
        # Server port
        self.config['server']['port'] = self._get_input(
            "Server port",
            self.config['server']['port'],
            self._validate_port,
            "Port must be between 1 and 65535"
        )
        
        # Enable authentication
        enable_auth = self._get_yes_no(
            "Enable authentication?",
            self.config['server'].getboolean('enable_auth', True)
        )
        self.config['server']['enable_auth'] = 'true' if enable_auth else 'false'
        
        # Auth token
        if enable_auth:
            print("\nAuthentication is enabled. You can use the following token:")
            print(f"Auth Token: {self.config['server']['auth_token']}")
            
            if self._get_yes_no("Generate a new auth token?", False):
                self.config['server']['auth_token'] = self._generate_auth_token()
                print(f"New Auth Token: {self.config['server']['auth_token']}")
            
            # Update client auth token to match if not set
            if not self.config['client']['auth_token']:
                self.config['client']['auth_token'] = self.config['server']['auth_token']
        
        # Max connections
        self.config['server']['max_connections'] = self._get_input(
            "Maximum simultaneous connections",
            self.config['server']['max_connections'],
            lambda x: x.isdigit() and int(x) > 0,
            "Must be a positive integer"
        )
        
        # Rate limit (requests per minute)
        self.config['server']['rate_limit'] = self._get_input(
            "Rate limit (requests per minute, 0 to disable)",
            self.config['server']['rate_limit'],
            lambda x: x.isdigit() and int(x) >= 0,
            "Must be a non-negative integer"
        )
        
        # Log level
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        print("\nAvailable log levels:")
        for i, level in enumerate(log_levels, 1):
            print(f"  {i}. {level}")
        
        log_level_idx = int(self._get_input(
            "Select log level",
            str(log_levels.index(self.config['server']['log_level']) + 1 
                if self.config['server']['log_level'] in log_levels else 2),
            lambda x: x.isdigit() and 1 <= int(x) <= len(log_levels),
            f"Please enter a number between 1 and {len(log_levels)}"
        )) - 1
        
        self.config['server']['log_level'] = log_levels[log_level_idx]
        
        # Log file
        self.config['server']['log_file'] = self._get_input(
            "Path to server log file",
            self.config['server']['log_file']
        )
    
    def _edit_client_settings(self):
        """Edit client settings interactively."""
        print("\n=== Client Settings ===\n")
        
        # Server URL
        self.config['client']['server_url'] = self._get_input(
            "Server URL (e.g., wss://your-server:8443)",
            self.config['client']['server_url'],
            self._validate_url,
            "Invalid URL format. Must start with ws:// or wss://"
        )
        
        # Local port
        self.config['client']['local_port'] = self._get_input(
            "Local SOCKS5 proxy port",
            self.config['client']['local_port'],
            self._validate_port,
            "Port must be between 1 and 65535"
        )
        
        # Auth token (if server auth is enabled)
        if self.config['server'].getboolean('enable_auth', True):
            print("\nServer authentication is enabled. Make sure to set the auth token.")
            print(f"Current auth token: {self.config['client']['auth_token']}")
            
            if self._get_yes_no("Update auth token?", False):
                self.config['client']['auth_token'] = self._get_input(
                    "Enter auth token",
                    self.config['client']['auth_token']
                )
        
        # Log level
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        print("\nAvailable log levels:")
        for i, level in enumerate(log_levels, 1):
            print(f"  {i}. {level}")
        
        log_level_idx = int(self._get_input(
            "Select log level",
            str(log_levels.index(self.config['client']['log_level']) + 1 
                if self.config['client']['log_level'] in log_levels else 2),
            lambda x: x.isdigit() and 1 <= int(x) <= len(log_levels),
            f"Please enter a number between 1 and {len(log_levels)}"
        )) - 1
        
        self.config['client']['log_level'] = log_levels[log_level_idx]
        
        # Log file
        self.config['client']['log_file'] = self._get_input(
            "Path to client log file",
            self.config['client']['log_file']
        )
    
    def _edit_tls_settings(self):
        """Edit TLS settings interactively."""
        print("\n=== TLS/SSL Settings ===\n")
        
        # Enable TLS
        enable_tls = self._get_yes_no(
            "Enable TLS/SSL encryption?",
            self.config['tls'].getboolean('enabled', True)
        )
        self.config['tls']['enabled'] = 'true' if enable_tls else 'false'
        
        if not enable_tls:
            print("\nWARNING: Disabling TLS is not recommended for production use!")
            return
        
        # Certificate file
        self.config['tls']['cert_file'] = self._get_input(
            "Path to SSL certificate file",
            self.config['tls']['cert_file']
        )
        
        # Private key file
        self.config['tls']['key_file'] = self._get_input(
            "Path to SSL private key file",
            self.config['tls']['key_file']
        )
        
        # CA file (optional)
        self.config['tls']['ca_file'] = self._get_input(
            "Path to CA certificate file (optional, for client certs)",
            self.config['tls']['ca_file'] or ''
        )
        
        # Verify peer
        verify_peer = self._get_yes_no(
            "Verify peer certificate?",
            self.config['tls'].getboolean('verify_peer', True)
        )
        self.config['tls']['verify_peer'] = 'true' if verify_peer else 'false'
        
        # Verify hostname
        verify_hostname = self._get_yes_no(
            "Verify hostname in certificate?",
            self.config['tls'].getboolean('verify_hostname', True)
        )
        self.config['tls']['verify_hostname'] = 'true' if verify_hostname else 'false'
    
    def _edit_security_settings(self):
        """Edit security settings interactively."""
        print("\n=== Security Settings ===\n")
        
        # Allowed IPs
        print("\nAllowed IPs (comma-separated, leave empty to allow all):")
        print("Example: 192.168.1.0/24, 10.0.0.1")
        self.config['security']['allowed_ips'] = self._get_input(
            "",
            self.config['security']['allowed_ips']
        )
        
        # Blocked IPs
        print("\nBlocked IPs (comma-separated, leave empty to block none):")
        print("Example: 192.168.1.100, 10.0.0.0/8")
        self.config['security']['blocked_ips'] = self._get_input(
            "",
            self.config['security']['blocked_ips']
        )
        
        # Brute force protection
        enable_bruteforce_protection = self._get_yes_no(
            "Enable brute force protection?",
            self.config['security'].getboolean('enable_bruteforce_protection', True)
        )
        self.config['security']['enable_bruteforce_protection'] = 'true' if enable_bruteforce_protection else 'false'
        
        if enable_bruteforce_protection:
            # Max auth attempts
            self.config['security']['max_auth_attempts'] = self._get_input(
                "Maximum authentication attempts before ban",
                self.config['security']['max_auth_attempts'],
                lambda x: x.isdigit() and int(x) > 0,
                "Must be a positive integer"
            )
            
            # Ban time (in seconds)
            ban_time = int(self._get_input(
                "Ban time (in minutes)",
                str(int(self.config['security']['ban_time']) // 60),
                lambda x: x.isdigit() and int(x) > 0,
                "Must be a positive integer"
            ))
            self.config['security']['ban_time'] = str(ban_time * 60)  # Convert to seconds
    
    def _edit_advanced_settings(self):
        """Edit advanced settings interactively."""
        print("\n=== Advanced Settings ===\n")
        
        # Buffer size
        self.config['advanced']['buffer_size'] = self._get_input(
            "Buffer size (bytes)",
            self.config['advanced']['buffer_size'],
            lambda x: x.isdigit() and int(x) >= 1024,
            "Must be at least 1024 bytes"
        )
        
        # Timeout
        self.config['advanced']['timeout'] = self._get_input(
            "Connection timeout (seconds)",
            self.config['advanced']['timeout'],
            lambda x: x.isdigit() and int(x) > 0,
            "Must be a positive integer"
        )
        
        # Keepalive
        self.config['advanced']['keepalive'] = self._get_input(
            "Keepalive interval (seconds, 0 to disable)",
            self.config['advanced']['keepalive'],
            lambda x: x.isdigit() and int(x) >= 0,
            "Must be a non-negative integer"
        )
        
        # Compression
        enable_compression = self._get_yes_no(
            "Enable compression?",
            self.config['advanced'].getboolean('compression', True)
        )
        self.config['advanced']['compression'] = 'true' if enable_compression else 'false'
        
        # Max message size
        self.config['advanced']['max_message_size'] = self._get_input(
            "Maximum message size (bytes)",
            self.config['advanced']['max_message_size'],
            lambda x: x.isdigit() and int(x) > 0,
            "Must be a positive integer"
        )
    
    def interactive_config(self):
        """Run interactive configuration wizard."""
        print("=== Anti-Filter Bridge Configuration Wizard ===\n")
        
        while True:
            print("\nMain Menu:")
            print("  1. Server Settings")
            print("  2. Client Settings")
            print("  3. TLS/SSL Settings")
            print("  4. Security Settings")
            print("  5. Advanced Settings")
            print("  6. Show Current Configuration")
            print("  7. Save Configuration")
            print("  8. Exit")
            
            choice = input("\nSelect an option (1-8): ").strip()
            
            if choice == '1':
                self._edit_server_settings()
            elif choice == '2':
                self._edit_client_settings()
            elif choice == '3':
                self._edit_tls_settings()
            elif choice == '4':
                self._edit_security_settings()
            elif choice == '5':
                self._edit_advanced_settings()
            elif choice == '6':
                self.show_config()
            elif choice == '7':
                output_file = input(f"Save configuration to [{self.config_file or 'config.ini'}]: ").strip()
                output_file = output_file or self.config_file or 'config.ini'
                
                if self.save_config(output_file):
                    print(f"\nConfiguration saved to {output_file}")
                    
                    # Update config file path if this is a new file
                    if not self.config_file or os.path.abspath(output_file) != os.path.abspath(self.config_file or ''):
                        self.config_file = output_file
                        self.loaded = True
            elif choice == '8':
                if self._get_yes_no("\nExit without saving?", False):
                    return
            else:
                print("Invalid choice. Please try again.")
    
    def show_config(self):
        """Display the current configuration."""
        print("\nCurrent Configuration:")
        print("=" * 80)
        
        for section in self.config.sections():
            print(f"\n[{section}]")
            for key, value in self.config[section].items():
                # Mask sensitive information
                if 'token' in key.lower() or 'password' in key.lower() or 'secret' in key.lower():
                    if value:
                        value = "*" * 8
                    else:
                        value = "(not set)"
                
                print(f"{key} = {value}")
        
        print("\n" + "=" * 80)
    
    def generate_config(self, output_file: str = None) -> bool:
        """Generate a configuration file.
        
        Args:
            output_file: Path to save the configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not output_file and not self.config_file:
            logger.error("No output file specified")
            return False
        
        output_file = output_file or self.config_file
        return self.save_config(output_file)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge Configuration Generator')
    
    parser.add_argument(
        '-c', '--config',
        help='Path to an existing config file to edit',
        default=None
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output configuration file',
        default=None
    )
    
    parser.add_argument(
        '-i', '--interactive',
        help='Run in interactive mode',
        action='store_true',
        default=False
    )
    
    parser.add_argument(
        '-s', '--show',
        help='Show the current configuration and exit',
        action='store_true',
        default=False
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the config generator."""
    args = parse_arguments()
    
    # Create config generator
    generator = ConfigGenerator(args.config)
    
    # Show config and exit if requested
    if args.show:
        generator.show_config()
        return 0
    
    # Interactive mode
    if args.interactive:
        generator.interactive_config()
    # Non-interactive mode (generate default config)
    else:
        output_file = args.output or args.config or 'config.ini'
        if generator.generate_config(output_file):
            print(f"Configuration generated: {output_file}")
            return 0
        else:
            logger.error("Failed to generate configuration")
            return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)
