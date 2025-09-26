from flask import Flask, request, jsonify
from blockchain import Blockchain
from wallet import (
    generate_rsa_keypair,
    serialize_public_key,
    serialize_private_key,
    sign_message,
    verify_signature,
    encrypt_with_public,
    decrypt_with_private,
    deserialize_public_key,
    load_private_key,
)
import requests, json, os

app = Flask(__name__)

NODE_PORT = int(os.environ.get("PORT", 5000))

# ---- Key management ----
key_file = f"node_keys_{NODE_PORT}.json"

if os.path.exists(key_file):
    with open(key_file, "r") as f:
        saved = json.load(f)
    priv = load_private_key(saved["private"])
    pub_pem_b64 = saved["public"]
else:
    priv, pub = generate_rsa_keypair()
    pub_pem_b64 = serialize_public_key(pub)
    with open(key_file, "w") as f:
        f.write(json.dumps({
            "private": serialize_private_key(priv),
            "public": pub_pem_b64
        }))

peers = set()
blockchain = Blockchain()

# ---- Endpoints ----
@app.route("/id", methods=["GET"])
def get_id():
    return jsonify({"public_key": pub_pem_b64, "port": NODE_PORT})

@app.route("/peers", methods=["GET"])
def get_peers():
    return jsonify(list(peers))

@app.route("/peers/register", methods=["POST"])
def register_peer():
    data = request.get_json()
    host = data.get("host")
    if host:
        peers.add(host)
    return jsonify({"peers": list(peers)})

@app.route("/tx/new", methods=["POST"])
def new_transactions():
    tx = request.get_json()
    try:
        sender_pub_b64 = tx["sender_pub"]
        sender_pub = deserialize_public_key(sender_pub_b64)
        signed_payload = (tx["from"] + tx["to"] + tx["message"]).encode()
        if not verify_signature(sender_pub, signed_payload, tx["signature"]):
            return jsonify({"message": "invalid signature"}), 400
    except Exception as e:
        return jsonify({"message": "signature error", "error": str(e)}), 400

    blockchain.add_transaction(tx)
    broadcast("/tx/receive", tx)
    return jsonify({"message": "tx added", "pending": len(blockchain.pending_transactions)}), 201

@app.route("/tx/receive", methods=["POST"])
def receive_tx():
    tx = request.get_json()
    blockchain.add_transaction(tx)
    return jsonify({"message": "tx received"}), 201

@app.route("/mine", methods=["POST"])
def mine():
    block = blockchain.mine()
    if block:
        broadcast("/block/receive", block)
        return jsonify(block), 201
    else:
        return jsonify({"message": "no transaction"}), 200

@app.route("/block/receive", methods=["POST"])
def receive_block():
    block = request.get_json()
    blockchain.chain.append(block_from_dict(block))
    return jsonify({"message": "block added"}), 201

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify([b.to_dict() for b in blockchain.chain])

@app.route("/pending", methods=["GET"])
def get_pending():
    """Return all pending (unmined) transactions."""
    return jsonify(blockchain.pending_transactions)

@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json()
    to = data["to_node"]
    to_pub = data["to_pub"]
    message = data["message"]

    recipient_pub = deserialize_public_key(to_pub)
    ciphertext = encrypt_with_public(recipient_pub, message)

    payload = {
        "from": f"http://127.0.0.1:{NODE_PORT}",
        "to": to,
        "message": ciphertext,
        "sender_pub": pub_pem_b64,
    }

    signed = sign_message(priv, (payload["from"] + payload["to"] + payload["message"]).encode())
    payload["signature"] = signed

    blockchain.add_transaction(payload)
    broadcast("/tx/receive", payload)

    return jsonify({"sent": True, "cipher": ciphertext}), 200

# ---- helpers ----
def block_from_dict(bdict):
    from blockchain import Block
    b = Block(
        bdict["index"],
        bdict["timestamp"],
        bdict["transactions"],
        bdict["prev_hash"],
        bdict["nonce"],
    )
    b.hash = bdict["hash"]
    return b

def broadcast(path, payload):
    for p in list(peers):
        try:
            requests.post(f"{p}{path}", json=payload, timeout=1)
        except Exception:
            pass

# ---- Run server ----
if __name__ == "__main__":
    raw_peers = os.environ.get("PEERS", "")
    if raw_peers:
        for p in raw_peers.split(","):
            peers.add(p)
    app.run(host="0.0.0.0", port=NODE_PORT)
