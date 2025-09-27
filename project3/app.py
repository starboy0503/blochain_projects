import tkinter as tk
from tkinter import messagebox, filedialog
from blockchain import Blockchain
from wallet_utils import BASE_DIR
import json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

blockchain = Blockchain()

class VotingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blockchain Voting System")
        self.logged_in_user = None
        self.user_role = None

        # Layout
        self.left_frame = tk.Frame(root, padx=20, pady=20)
        self.left_frame.pack(side="left", fill="y")

        self.right_frame = tk.Frame(root, padx=20, pady=20, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="both", expand=True)

        # ---------------- Left Frame: Login + Voting ----------------
        tk.Label(self.left_frame, text="Login with your JSON file:").pack(pady=5)
        tk.Button(self.left_frame, text="Select JSON File", command=self.login).pack(pady=5)

        self.candidate_var = tk.StringVar(value="Alice")
        self.vote_frame = tk.Frame(self.left_frame)

        tk.Label(self.vote_frame, text="Select Candidate:").pack()
        for cand in ["Alice", "Bob", "Charlie"]:
            tk.Radiobutton(
                self.vote_frame, text=cand,
                variable=self.candidate_var, value=cand
            ).pack(anchor="w")

        tk.Button(self.vote_frame, text="✅ Cast Vote", command=self.cast_vote, bg="lightgreen").pack(pady=5, fill="x")
        tk.Button(self.vote_frame, text="⛏️ Mine Block", command=self.mine_block, bg="lightblue").pack(pady=5, fill="x")

        # ---------------- Right Frame: Officer Dashboard ----------------
        tk.Label(self.right_frame, text="Voting Dashboard", font=("Arial", 14, "bold"), bg="#f0f0f0").pack()

        tk.Label(self.right_frame, text="Voters who have voted:", bg="#f0f0f0").pack(anchor="w")
        self.voters_listbox = tk.Listbox(self.right_frame, height=8, width=40)
        self.voters_listbox.pack(pady=5)

        tk.Label(self.right_frame, text="Current Tally:", bg="#f0f0f0").pack(anchor="w")
        self.tally_text = tk.Text(self.right_frame, height=8, width=40)
        self.tally_text.pack(pady=5)

        self.graph_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        self.graph_frame.pack(pady=10, fill="both", expand=True)

        # Refresh button
        self.refresh_btn = tk.Button(self.right_frame, text="🔄 Refresh Dashboard", command=self.update_dashboard, bg="orange")
        self.refresh_btn.pack(pady=5, fill="x")

        self.right_frame.pack_forget()  # Hide dashboard until officer logs in

    def login(self):
        # Let user pick their JSON file
        path = filedialog.askopenfilename(
            initialdir=BASE_DIR,
            title="Select your voter/officer JSON file",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*"))
        )
        if not path:
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid file format.\n{e}")
            return

        self.logged_in_user = data["name"]
        self.user_role = data.get("role", "student")

        if self.user_role == "student":
            messagebox.showinfo("Login Success", f"Welcome {self.logged_in_user} (Student)")
            self.vote_frame.pack(pady=10)
        elif self.user_role == "officer":
            messagebox.showinfo("Login Success", f"Welcome {self.logged_in_user} (Officer)")
            self.right_frame.pack(side="right", fill="both", expand=True)
            self.update_dashboard()
        else:
            messagebox.showerror("Error", "Unknown role in JSON file")

    def cast_vote(self):
        if not self.logged_in_user or self.user_role != "student":
            messagebox.showerror("Error", "Login as student first!")
            return

        candidate = self.candidate_var.get()
        success = blockchain.add_vote(self.logged_in_user, candidate)

        if success:
            messagebox.showinfo("Vote Cast", f"Vote recorded for {candidate}")
        else:
            messagebox.showerror("Error", "You have already voted!")

    def mine_block(self):
        block = blockchain.mine_block()
        if block:
            messagebox.showinfo("Block Mined", f"Block {block['index']} added to chain!")
        else:
            messagebox.showwarning("No Votes", "No pending votes to mine.")

        if self.user_role == "officer":
            self.update_dashboard()

    def update_dashboard(self):
        # Update voters list
        self.voters_listbox.delete(0, tk.END)
        voters_seen = set()
        for block in blockchain.chain:
            for vote in block['votes']:
                if vote['voter_id'] not in voters_seen:
                    self.voters_listbox.insert(tk.END, vote['voter_id'])
                    voters_seen.add(vote['voter_id'])

        # Update tally
        self.tally_text.delete(1.0, tk.END)
        tally = blockchain.get_tally()
        if tally:
            for cand, count in tally.items():
                self.tally_text.insert(tk.END, f"{cand}: {count}\n")
        else:
            self.tally_text.insert(tk.END, "No votes yet.")

        # Update graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        if tally:
            fig, ax = plt.subplots(figsize=(4, 3))
            candidates = list(tally.keys())
            votes = list(tally.values())
            ax.bar(candidates, votes, color=["blue", "green", "red"])
            ax.set_title("Vote Count per Candidate")
            ax.set_ylabel("Votes")
            ax.set_xlabel("Candidates")
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = VotingApp(root)
    root.mainloop()
