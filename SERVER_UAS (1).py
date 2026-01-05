import socket
import threading
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext


class ChatServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Server - Control Panel")
        self.root.geometry("800x600")

        # ================= GUI =================
        self.text_area = scrolledtext.ScrolledText(
            root, height=25, width=90, state="normal"
        )
        self.text_area.pack(padx=10, pady=10)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.start_button = tk.Button(
            button_frame, text="Start Server", command=self.start_server
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(
            button_frame, text="Stop Server",
            command=self.stop_server, state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.clear_button = tk.Button(
            button_frame, text="Clear Log", command=self.clear_log
        )
        self.clear_button.grid(row=0, column=2, padx=5)

        # ================= SERVER =================
        self.host = "0.0.0.0"
        self.port = 5555
        self.server_socket = None
        self.server_running = False

        self.clients = {}          # {client_id: socket}
        self.client_lock = threading.Lock()

    # ================= GUI UTILIASI =================
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(
            0, lambda: self._append_log(timestamp, message)
        )

    def _append_log(self, timestamp, message):
        self.text_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_area.see(tk.END)

    def clear_log(self):
        self.text_area.delete("1.0", tk.END)

    # ================= SERVER CONTROL =================
    def start_server(self):
        try:
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)

            self.server_running = True

            self.log_message(
                f"Server started on {self.host}:{self.port}"
            )

            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            threading.Thread(
                target=self.accept_clients,
                daemon=True
            ).start()

        except Exception as e:
            self.log_message(f"Error starting server: {e}")

    def stop_server(self):
        self.server_running = False

        try:
            self.server_socket.close()
        except:
            pass

        with self.client_lock:
            for sock in self.clients.values():
                try:
                    sock.close()
                except:
                    pass
            self.clients.clear()

        self.log_message("Server stopped")

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    # ================= CLIENT HANDLING =================
    def accept_clients(self):
        while self.server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except:
                break

    def handle_client(self, client_socket, addr):
        client_id = None
        try:
            client_id = client_socket.recv(1024).decode().strip()

            with self.client_lock:
                if client_id in self.clients:
                    client_socket.send(
                        "ERROR: ID already in use".encode()
                    )
                    client_socket.close()
                    return
                self.clients[client_id] = client_socket

            self.log_message(
                f"{client_id} connected from {addr}"
            )

            while self.server_running:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                # LIST CLIENTS
                if data == "LIST":
                    with self.client_lock:
                        client_list = ",".join(self.clients.keys())
                    client_socket.send(
                        f"CLIENTS:{client_list}".encode()
                    )
                    continue

                # BROADCAST
                if data.startswith("ALL:"):
                    message = data[4:]
                    self.broadcast_message(
                        f"{client_id} (ALL): {message}",
                        sender_id=client_id
                    )
                    self.log_message(
                        f"{client_id} (ALL): {message}"
                    )

                # PRIVATE MESSAGE
                else:
                    try:
                        _, target_id, message = data.split(":", 2)
                        self.send_private_message(
                            target_id,
                            f"{client_id}: {message}"
                        )
                        self.log_message(
                            f"{client_id} -> {target_id}: {message}"
                        )
                    except:
                        client_socket.send(
                            "ERROR: Use TO:ClientID:Message".encode()
                        )

        except Exception as e:
            self.log_message(f"Client error: {e}")

        finally:
            with self.client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]

            try:
                client_socket.close()
            except:
                pass

            self.log_message(f"{client_id} disconnected")

    # ================= MESSAGE ROUTING =================
    def send_private_message(self, target_id, message):
        with self.client_lock:
            if target_id in self.clients:
                self.clients[target_id].send(message.encode())

    def broadcast_message(self, message, sender_id=None):
        with self.client_lock:
            for cid, sock in self.clients.items():
                if cid != sender_id:
                    sock.send(message.encode())


# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatServerGUI(root)
    root.mainloop()
