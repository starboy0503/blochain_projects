import sys
import requests
import tkinter as tk
from tkinter import scrolledtext, ttk
import json, os
from wallet import load_private_key, decrypt_with_private

# --- Detect or select node ---
def detect_node():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        url = f"http://127.0.0.1:{port}"
        try:
            r = requests.get(url + "/id", timeout=1)
            if r.status_code == 200:
                print(f"✅ Connected to node at {url} (manual selection)")
                return url, port
        except Exception as e:
            print(f"❌ Node not running at {url}: {e}")
            sys.exit(1)

    # Otherwise auto-detect
    for port in range(5000, 5010):
        url = f"http://127.0.0.1:{port}"
        try:
            r = requests.get(url + "/id", timeout=1)
            if r.status_code == 200:
                print(f"✅ Auto-detected node at {url}")
                return url, port
        except:
            continue
    print("❌ No node found. Make sure node.py is running.")
    sys.exit(1)

NODE, NODE_PORT = detect_node()

# --- Load private key for this node ---
try:
    key_file = os.path.join(os.path.dirname(__file__), f"node_keys_{NODE_PORT}.json")
    if not os.path.exists(key_file):
        key_file = os.path.join(os.path.dirname(__file__), "node_keys.json")

    with open(key_file, "r") as f:
        saved = json.load(f)
    priv = load_private_key(saved["private"])
    print(f"🔑 Loaded key from {key_file}")
except Exception as e:
    print("❌ Could not load private key:", e)
    sys.exit(1)

# --- Tkinter UI ---
class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Blockchain Chat Client – {NODE}")

        # Two panes: outgoing & incoming
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        self.my_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=40, height=20, fg="green")
        self.my_log.pack(side=tk.LEFT, padx=5)
        self.my_log.insert(tk.END, "📤 Outgoing Messages\n")

        self.peer_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=40, height=20, fg="blue")
        self.peer_log.pack(side=tk.LEFT, padx=5)
        self.peer_log.insert(tk.END, "📥 Incoming Messages\n")

        # Input & controls
        bottom = tk.Frame(root)
        bottom.pack(pady=5)

        self.entry = tk.Entry(bottom, width=40)
        self.entry.pack(side=tk.LEFT, padx=5)

        self.send_btn = tk.Button(bottom, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.mine_btn = tk.Button(bottom, text="Mine", command=self.mine_block)
        self.mine_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(bottom, text="Peers", command=self.fetch_peers)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.peer_selector = ttk.Combobox(bottom, width=30)
        self.peer_selector.pack(side=tk.LEFT, padx=5)

        self.my_log.insert(tk.END, f"Connected to {NODE}\n")

    def fetch_peers(self):
        try:
            r = requests.get(f"{NODE}/peers")
            peer_list = r.json()
            if not peer_list:
                self.my_log.insert(tk.END, "⚠️ No peers found.\n")
            else:
                self.peer_selector["values"] = peer_list
                self.my_log.insert(tk.END, "Peers: " + str(peer_list) + "\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Error fetching peers: {e}\n")

    def send_message(self):
        text = self.entry.get().strip()
        peer_url = self.peer_selector.get().strip()
        if not text:
            return
        if not peer_url:
            self.my_log.insert(tk.END, "⚠️ Select a peer first!\n")
            return
        try:
            id_info = requests.get(f"{peer_url}/id").json()
            payload = {
                "to_node": peer_url,
                "to_pub": id_info["public_key"],
                "message": text,
            }
            r = requests.post(f"{NODE}/send", json=payload)
            if r.status_code == 200:
                self.my_log.insert(tk.END, f"You → {peer_url}: {text}\n")
                self.entry.delete(0, tk.END)
            else:
                self.my_log.insert(tk.END, f"Error sending: {r.text}\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Send failed: {e}\n")

    def mine_block(self):
        try:
            r = requests.post(f"{NODE}/mine")
            if r.status_code == 201:
                self.my_log.insert(tk.END, "⛏️ Block mined!\n")
            else:
                self.my_log.insert(tk.END, f"Mining: {r.json()}\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Mining failed: {e}\n")

    def fetch_inbox(self):
        try:
            r = requests.get(f"{NODE}/chain")
            chain = r.json()
            self.peer_log.delete(1.0, tk.END)
            self.peer_log.insert(tk.END, "📥 Incoming Messages\n")
            for block in chain:
                for tx in block.get("transactions", []):
                    if tx.get("to") == NODE:  # message meant for me
                        try:
                            plaintext = decrypt_with_private(priv, tx["message"])
                        except Exception:
                            plaintext = "[Decryption failed]"
                        self.peer_log.insert(tk.END, f"{tx['from']} → You: {plaintext}\n")
        except Exception as e:
            self.peer_log.insert(tk.END, f"Error fetching inbox: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)

    # auto-refresh inbox every 5 seconds
    def refresh_inbox():
        app.fetch_inbox()
        root.after(5000, refresh_inbox)

    refresh_inbox()
    root.mainloop()
import sys
import requests
import tkinter as tk
from tkinter import scrolledtext, ttk
import json, os
from wallet import load_private_key, decrypt_with_private

# --- Detect or select node ---
def detect_node():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        url = f"http://127.0.0.1:{port}"
        try:
            r = requests.get(url + "/id", timeout=1)
            if r.status_code == 200:
                print(f"✅ Connected to node at {url} (manual selection)")
                return url, port
        except Exception as e:
            print(f"❌ Node not running at {url}: {e}")
            sys.exit(1)

    # Otherwise auto-detect
    for port in range(5000, 5010):
        url = f"http://127.0.0.1:{port}"
        try:
            r = requests.get(url + "/id", timeout=1)
            if r.status_code == 200:
                print(f"✅ Auto-detected node at {url}")
                return url, port
        except:
            continue
    print("❌ No node found. Make sure node.py is running.")
    sys.exit(1)

NODE, NODE_PORT = detect_node()

# --- Load private key for this node ---
try:
    key_file = os.path.join(os.path.dirname(__file__), f"node_keys_{NODE_PORT}.json")
    if not os.path.exists(key_file):
        key_file = os.path.join(os.path.dirname(__file__), "node_keys.json")

    with open(key_file, "r") as f:
        saved = json.load(f)
    priv = load_private_key(saved["private"])
    print(f"🔑 Loaded key from {key_file}")
except Exception as e:
    print("❌ Could not load private key:", e)
    sys.exit(1)

# --- Tkinter UI ---
class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Blockchain Chat Client – {NODE}")

        # Two panes: outgoing & incoming
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        self.my_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=40, height=20, fg="green")
        self.my_log.pack(side=tk.LEFT, padx=5)
        self.my_log.insert(tk.END, "📤 Outgoing Messages\n")

        self.peer_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=40, height=20, fg="blue")
        self.peer_log.pack(side=tk.LEFT, padx=5)
        self.peer_log.insert(tk.END, "📥 Incoming Messages\n")

        # Input & controls
        bottom = tk.Frame(root)
        bottom.pack(pady=5)

        self.entry = tk.Entry(bottom, width=40)
        self.entry.pack(side=tk.LEFT, padx=5)

        self.send_btn = tk.Button(bottom, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.mine_btn = tk.Button(bottom, text="Mine", command=self.mine_block)
        self.mine_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(bottom, text="Peers", command=self.fetch_peers)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.peer_selector = ttk.Combobox(bottom, width=30)
        self.peer_selector.pack(side=tk.LEFT, padx=5)

        self.my_log.insert(tk.END, f"Connected to {NODE}\n")

    def fetch_peers(self):
        try:
            r = requests.get(f"{NODE}/peers")
            peer_list = r.json()
            if not peer_list:
                self.my_log.insert(tk.END, "⚠️ No peers found.\n")
            else:
                self.peer_selector["values"] = peer_list
                self.my_log.insert(tk.END, "Peers: " + str(peer_list) + "\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Error fetching peers: {e}\n")

    def send_message(self):
        text = self.entry.get().strip()
        peer_url = self.peer_selector.get().strip()
        if not text:
            return
        if not peer_url:
            self.my_log.insert(tk.END, "⚠️ Select a peer first!\n")
            return
        try:
            id_info = requests.get(f"{peer_url}/id").json()
            payload = {
                "to_node": peer_url,
                "to_pub": id_info["public_key"],
                "message": text,
            }
            r = requests.post(f"{NODE}/send", json=payload)
            if r.status_code == 200:
                self.my_log.insert(tk.END, f"You → {peer_url}: {text}\n")
                self.entry.delete(0, tk.END)
            else:
                self.my_log.insert(tk.END, f"Error sending: {r.text}\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Send failed: {e}\n")

    def mine_block(self):
        try:
            r = requests.post(f"{NODE}/mine")
            if r.status_code == 201:
                self.my_log.insert(tk.END, "⛏️ Block mined!\n")
            else:
                self.my_log.insert(tk.END, f"Mining: {r.json()}\n")
        except Exception as e:
            self.my_log.insert(tk.END, f"Mining failed: {e}\n")

    def fetch_inbox(self):
        self.peer_log.delete(1.0, tk.END)
        self.peer_log.insert(tk.END, "📥 Incoming Messages\n")

        # Confirmed (mined) messages
        try:
            r = requests.get(f"{NODE}/chain")
            chain = r.json()
            for block in chain:
                for tx in block.get("transactions", []):
                    if tx.get("to") == NODE:  # message meant for me
                        try:
                            plaintext = decrypt_with_private(priv, tx["message"])
                        except Exception:
                            plaintext = "[Decryption failed]"
                        self.peer_log.insert(tk.END, f"{tx['from']} → You: {plaintext}\n")
        except Exception as e:
            self.peer_log.insert(tk.END, f"Error fetching chain: {e}\n")

        # Pending (unmined) messages
        try:
            r = requests.get(f"{NODE}/pending")
            pending = r.json()
            for tx in pending:
                if tx.get("to") == NODE:
                    try:
                        plaintext = decrypt_with_private(priv, tx["message"])
                    except Exception:
                        plaintext = "[Decryption failed]"
                    self.peer_log.insert(tk.END, f"(pending) {tx['from']} → You: {plaintext}\n")
        except Exception as e:
            self.peer_log.insert(tk.END, f"Error fetching pending: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)

    # auto-refresh inbox every 5 seconds
    def refresh_inbox():
        app.fetch_inbox()
        root.after(5000, refresh_inbox)

    refresh_inbox()
    root.mainloop()
