from OpenSSL import crypto
import os

# Create a key pair
k = crypto.PKey()
k.generate_key(crypto.TYPE_RSA, 2048)

# Create a self-signed cert
cert = crypto.X509()
cert.get_subject().C = "IR"
cert.get_subject().ST = "Tehran"
cert.get_subject().L = "Tehran"
cert.get_subject().O = "Anti-Filter Bridge"
cert.get_subject().OU = "Development"
cert.get_subject().CN = "localhost"
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
cert.set_issuer(cert.get_subject())
cert.set_pubkey(k)
cert.sign(k, 'sha256')

# Create the certs directory if it doesn't exist
os.makedirs('certs', exist_ok=True)

# Save certificate
with open('certs/cert.pem', 'wb') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

# Save private key
with open('certs/key.pem', 'wb') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

print("✅ Generated certificate and key in certs/ directory")
