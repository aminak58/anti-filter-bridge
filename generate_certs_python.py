"""
Generate self-signed SSL certificates using Python cryptography library.
"""
import os
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CERT_DIR = Path('certs')
CERT_FILE = CERT_DIR / 'cert.pem'
KEY_FILE = CERT_DIR / 'key.pem'
DAYS_VALID = 365

def generate_self_signed_cert():
    """Generate a self-signed SSL certificate using Python cryptography."""
    
    # Create the certs directory if it doesn't exist
    CERT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Anti-Filter Bridge"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=DAYS_VALID)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            content_commitment=False,
            data_encipherment=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,
            ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=True,
    ).sign(private_key, hashes.SHA256())
    
    # Write private key
    with open(KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"✅ Generated private key: {KEY_FILE}")
    
    # Write certificate
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"✅ Generated self-signed certificate: {CERT_FILE}")
    
    print(f"\n🔐 Certificate details:")
    print(f"  Subject: {cert.subject}")
    print(f"  Issuer: {cert.issuer}")
    print(f"  Valid from: {cert.not_valid_before}")
    print(f"  Valid until: {cert.not_valid_after}")
    print(f"  Serial number: {cert.serial_number}")
    
    return True

if __name__ == "__main__":
    print("🔐 Generating self-signed SSL certificate using Python...\n")
    
    try:
        generate_self_signed_cert()
        print("\n✨ Certificate generation completed successfully!")
        print(f"\nTo use these certificates with the server, run:")
        print(f"  python -m anti_filter_bridge.server --certfile {CERT_FILE} --keyfile {KEY_FILE}")
        print("\nFor the client, you may need to use the --insecure flag")
        print("or add the certificate to your system's trust store.")
    except Exception as e:
        print(f"❌ Error generating certificate: {e}")
        exit(1)
