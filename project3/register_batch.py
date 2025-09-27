import tkinter as tk
from tkinter import messagebox
from wallet_utils import save_student, save_officer, BASE_DIR
import os, json, csv

class BatchRegisterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Voter Registration")

        self.voter_count = 0
        self.entries = []

        # Step 1: Enter number of voters
        tk.Label(root, text="Enter number of voters:").pack()
        self.count_entry = tk.Entry(root)
        self.count_entry.pack()

        tk.Button(root, text="Next", command=self.create_name_inputs).pack(pady=5)

        self.names_frame = tk.Frame(root)
        self.names_frame.pack(pady=10)

        # Officer key generation button
        tk.Button(root, text="Generate Officer Key", command=self.register_officer).pack(pady=5)

    def create_name_inputs(self):
        try:
            self.voter_count = int(self.count_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")
            return

        if self.voter_count <= 0:
            messagebox.showerror("Error", "Number of voters must be at least 1!")
            return

        # Clear old entries if re-used
        for widget in self.names_frame.winfo_children():
            widget.destroy()
        self.entries = []

        tk.Label(self.names_frame, text=f"Enter {self.voter_count} voter names:").pack()

        for i in range(self.voter_count):
            entry = tk.Entry(self.names_frame)
            entry.pack(pady=2)
            self.entries.append(entry)

        tk.Button(self.names_frame, text="Register All", command=self.register_all).pack(pady=10)

    def register_all(self):
        csv_path = os.path.join(BASE_DIR, "all_voters.csv")

        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Name", "Private Key", "Public Key"])  # header row

            for entry in self.entries:
                name = entry.get().strip()
                if not name:
                    messagebox.showerror("Error", "All voter names are required!")
                    return
                path = save_student(name)

                # read JSON to export keys into CSV
                with open(path, "r") as f:
                    data = json.load(f)
                    writer.writerow([data["name"], data["private_key"], data["public_key"]])

        messagebox.showinfo(
            "Success",
            f"✅ All voters registered!\n\nJSON + CSV saved in '{BASE_DIR}'"
        )

    def register_officer(self):
        path = save_officer("officer")
        messagebox.showinfo("Success", f"✅ Officer key generated!\nSaved at {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchRegisterApp(root)
    root.mainloop()
