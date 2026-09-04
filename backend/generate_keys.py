#!/usr/bin/env python3
"""
Generate RSA key pair for passport signing.
This script creates a private key and public key, then encodes them in base64
for storage in environment variables.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import base64

# Generate RSA private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Serialize private key to PEM format
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get public key
public_key = private_key.public_key()

# Serialize public key to PEM format
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Encode in base64 for environment variables
private_key_b64 = base64.b64encode(private_pem).decode('utf-8')
public_key_b64 = base64.b64encode(public_pem).decode('utf-8')

print("=" * 80)
print("GENERATED CRYPTOGRAPHIC KEYS")
print("=" * 80)
print("\nAdd these to your .env file:\n")
print(f"SIGNING_PRIVATE_KEY_B64={private_key_b64}")
print(f"\nSIGNING_PUBLIC_KEY_B64={public_key_b64}")
print("\n" + "=" * 80)
print("\nPrivate Key (PEM format):")
print(private_pem.decode('utf-8'))
print("\nPublic Key (PEM format):")
print(public_pem.decode('utf-8'))
print("=" * 80)