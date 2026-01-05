import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        self.root.geometry("700x550")

        # ================= CONNECTION =================
        self.host = "10.159.120.120"
        self.port = 5555
        self.client_socket = None
        self.connected = False

        # ================= GUI =================
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        tk.Label(top_frame, text="Client ID:").grid(row=0, column=0)
        self.id_entry = tk.Entry(top_frame, width=15)
        self.id_entry.grid(row=0, column=1, padx=5)

        self.connect_button = tk.Button(
            top_frame, text="Connect", command=self.connect_to_server
        )
        self.connect_button.grid(row=0, column=2, padx=5)

        # Chat display
        self.chat_area = scrolledtext.ScrolledText(
            root, height=20, width=80, state="normal"
        )
        self.chat_area.pack(padx=10, pady=10)

        # Message input
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=5)

        self.message_entry = tk.Entry(bottom_frame, width=50)
        self.message_entry.grid(row=0, column=0, padx=5)

        # Target ID (private)
        self.target_entry = tk.Entry(bottom_frame, width=15)
        self.target_entry.grid(row=0, column=1, padx=5)
        self.target_entry.insert(0, "Target ID")

        self.send_private_btn = tk.Button(
            bottom_frame, text="Send Private", command=self.send_private
        )
        self.send_private_btn.grid(row=0, column=2, padx=5)

        self.send_all_btn = tk.Button(
            bottom_frame, text="Send All", command=self.send_broadcast
        )
        self.send_all_btn.grid(row=0, column=3, padx=5)

    # ================= UTIL =================
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(
            0,
            lambda: self.chat_area.insert(
                tk.END, f"[{timestamp}] {message}\n"
            )
        )
        self.chat_area.see(tk.END)

    # ================= CONNECTION =================
    def connect_to_server(self):
        client_id = self.id_entry.get().strip()
        if not client_id:
            self.log_message("Client ID cannot be empty")
            return

        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.client_socket.connect((self.host, self.port))

            # Send ID to server
            self.client_socket.send(client_id.encode())

            self.connected = True
            self.log_message("Connected to server")

            self.connect_button.config(state="disabled")

            threading.Thread(
                target=self.receive_messages,
                daemon=True
            ).start()

        except Exception as e:
            self.log_message(f"Connection error: {e}")

    # ================= RECEIVE =================
    def receive_messages(self):
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                self.log_message(data)
            except:
                break

        self.log_message("Disconnected from server")
        self.connected = False

    # ================= SEND =================
    def send_broadcast(self):
        if not self.connected:
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        self.client_socket.send(f"ALL:{message}".encode())
        self.log_message(f"You (ALL): {message}")
        self.message_entry.delete(0, tk.END)

    def send_private(self):
        if not self.connected:
            return

        target = self.target_entry.get().strip()
        message = self.message_entry.get().strip()

        if not target or not message:
            return

        self.client_socket.send(
            f"TO:{target}:{message}".encode()
        )
        self.log_message(f"You -> {target}: {message}")
        self.message_entry.delete(0, tk.END)


# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
