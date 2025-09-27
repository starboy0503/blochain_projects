import json, os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# ✅ Absolute base path
BASE_DIR = "/Users/adityadhanrajsingh/Desktop/blockchain/project3/"

os.makedirs(BASE_DIR, exist_ok=True)

def generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return private_pem, public_pem

def save_student(name):
    private_key, public_key = generate_keypair()
    data = {
        "role": "student",
        "name": name,
        "private_key": private_key,
        "public_key": public_key,
        "has_voted": False
    }
    path = os.path.join(BASE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    return path

def save_officer(name="officer"):
    private_key, public_key = generate_keypair()
    data = {
        "role": "officer",
        "name": name,
        "private_key": private_key,
        "public_key": public_key
    }
    path = os.path.join(BASE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    return path
