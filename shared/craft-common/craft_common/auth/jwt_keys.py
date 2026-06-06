import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def get_or_create_jwt_keys(base_dir: Path):
    keys_dir = base_dir / '.devops' / 'keys'
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    private_key_path = keys_dir / 'jwt_private.pem'
    public_key_path = keys_dir / 'jwt_public.pem'
    
    if not private_key_path.exists() or not public_key_path.exists():
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Save private key
        with open(private_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # Generate public key
        public_key = private_key.public_key()
        
        # Save public key
        with open(public_key_path, 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
            
    with open(private_key_path, 'r') as f:
        private_key_str = f.read()
        
    with open(public_key_path, 'r') as f:
        public_key_str = f.read()
        
    return private_key_str, public_key_str
