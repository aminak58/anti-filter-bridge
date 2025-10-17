"""
Generate self-signed SSL certificates for testing the Anti-Filter Bridge.

This script creates a self-signed certificate and private key that can be used
for testing the WebSocket server and client with TLS/SSL encryption.
"""
import os
import ssl
import subprocess
import sys
from pathlib import Path

# Configuration
CERT_DIR = Path('certs')
CERT_FILE = CERT_DIR / 'cert.pem'
KEY_FILE = CERT_DIR / 'key.pem'
DAYS_VALID = 365  # Certificate validity in days
KEY_SIZE = 2048    # RSA key size in bits

def generate_self_signed_cert(common_name: str = 'localhost', alt_names: list = None):
    """
    Generate a self-signed SSL certificate and private key.
    
    Args:
        common_name: The common name (CN) for the certificate
        alt_names: List of subject alternative names (SANs)
    """
    # Create the certs directory if it doesn't exist
    CERT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Prepare subject alternative names
    san_extension = ''
    if alt_names:
        san_list = [f'DNS:{name}' for name in alt_names if ':' not in name]
        san_list.extend([f'IP:{name}' for name in alt_names if ':' in name])
        san_extension = f'-addext subjectAltName={','.join(san_list)}'
    
    # Generate the private key and certificate
    try:
        # Generate private key
        subprocess.run(
            ['openssl', 'genrsa', '-out', str(KEY_FILE), str(KEY_SIZE)],
            check=True,
            capture_output=True
        )
        print(f"✅ Generated private key: {KEY_FILE}")
        
        # Generate self-signed certificate
        cmd = [
            'openssl', 'req', '-new', '-x509',
            '-key', str(KEY_FILE),
            '-out', str(CERT_FILE),
            '-days', str(DAYS_VALID),
            '-subj', f'/CN={common_name}',
            '-addext', 'keyUsage=digitalSignature,keyEncipherment',
            '-addext', 'extendedKeyUsage=serverAuth,clientAuth'
        ]
        
        if san_extension:
            cmd.extend(san_extension.split())
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Generated self-signed certificate: {CERT_FILE}")
        
        # Set file permissions
        KEY_FILE.chmod(0o600)
        CERT_FILE.chmod(0o644)
        
        print("\n🔐 Certificate details:")
        subprocess.run(['openssl', 'x509', '-in', str(CERT_FILE), '-noout', '-text'])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificate: {e}")
        if e.stderr:
            print(e.stderr.decode())
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def verify_certificate():
    """Verify the generated certificate and key pair."""
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        print("❌ Certificate or key file not found")
        return False
    
    try:
        # Verify the certificate can be loaded
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)
        print("✅ Certificate and key are valid and can be loaded")
        return True
    except Exception as e:
        print(f"❌ Error loading certificate: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Generating self-signed SSL certificate for testing...\n")
    
    # Default subject alternative names
    alt_names = [
        'localhost',
        '127.0.0.1',
        '::1',
    ]
    
    # Generate the certificate
    generate_self_signed_cert(common_name='localhost', alt_names=alt_names)
    
    # Verify the certificate
    print("\n🔍 Verifying certificate...")
    if not verify_certificate():
        sys.exit(1)
    
    print("\n✨ Certificate generation completed successfully!")
    print(f"\nTo use these certificates with the server, run:")
    print(f"  python -m anti_filter_bridge.server --certfile {CERT_FILE} --keyfile {KEY_FILE}")
    print("\nFor the client, you may need to use the --insecure flag")
    print("or add the certificate to your system's trust store.")
