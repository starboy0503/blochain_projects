from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64


def generate_rsa_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    return priv, pub
# generated a 2048 bit RSA key pair returns both private and pubic key

def serialize_public_key(pub):
    return base64.b64encode(pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )).decode()
# turn public key into PEM format -> then base64 encodes ->returns a string useful to store/send over network

def deserialize_public_key(b64):
    pem = base64.b64decode(b64.encode())
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    return load_pem_public_key(pem)
# base64 string → PEM → real public_key object

def serialize_private_key(priv, password=None):
    if isinstance(password, str):   # auto-convert string passwords
        password = password.encode()
    enc = serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
    return base64.b64encode(priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc
    )).decode()
# converts private key into PEM format
# If password provided, encrypts the key 
# encode into base64 for storage

def load_private_key(b64, password=None):
    if isinstance(password, str):   # handle string passwords
        password = password.encode()
    pem = base64.b64decode(b64.encode())
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    return load_pem_private_key(pem, password=password)
# loads a private key back from a base64 string 
# needs password if key was encrypted

def sign_message(priv, message: bytes):
    sig = priv.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(sig).decode()
# signs a message with the private key using RSA-PSS+SHA256
# returns the signature as base64 text

def verify_signature(pub, message: bytes, signature_64: str) -> bool:
    sig = base64.b64decode(signature_64.encode())
    try:
        pub.verify(sig, message,
                   padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                   hashes.SHA256()
        )
        return True
    except Exception:
        return False
# take a message + signature + public key
# verifies if signature is valid 
# return true if correct else false

def encrypt_with_public(pub, plaintext: str) -> str:
    ct = pub.encrypt(
        plaintext.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return base64.b64encode(ct).decode()
# encrypts a string with a public key using RSA-OAEP+SHA256
# output is base64 ciphertext

def decrypt_with_private(priv, ciphertext_b64: str) -> str:
    ct = base64.b64decode(ciphertext_b64.encode())
    pt = priv.decrypt(
        ct,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return pt.decode()
# decrypts cipher text with private key
# returns original string
