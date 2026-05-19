import json
import socket
import threading

HOST = "0.0.0.0"
PORT = 5000


class TeacherServer:
    """Класс сервера для управления компьютерами студентов."""

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.lock = threading.Lock()
        self.gui_app = None
        self.active_streams = {}  # {addr: RemoteControlWindow}

    def start_server(self, ui_callback):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        threading.Thread(target=self._accept_connections, args=(ui_callback,), daemon=True).start()

    def _accept_connections(self, ui_callback):
        while True:
            try:
                client_sock, addr = self.server_socket.accept()
                data = client_sock.recv(1024).decode("utf-8")
                client_info = json.loads(data)
                username = client_info.get("username", str(addr))

                with self.lock:
                    self.clients[addr] = (client_sock, username)

                ui_callback()
                threading.Thread(target=self._listen_client, args=(client_sock, addr, ui_callback), daemon=True).start()
            except Exception:
                break

    def _listen_client(self, client_sock, addr, ui_callback):
        buffer = ""
        while True:
            try:
                data = client_sock.recv(1024 * 64).decode("utf-8")
                if not data: raise ConnectionResetError
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip(): continue
                    
                    payload = json.loads(line)
                    # Если пришел очередной кадр стрима, отдаем его в соответствующее окно
                    if payload.get("action") == "screenshot_data":
                        if addr in self.active_streams:
                            window = self.active_streams[addr]
                            self.gui_app.after(0, window.update_frame, payload.get("image"))
            except (ConnectionResetError, socket.error, json.JSONDecodeError):
                with self.lock:
                    if addr in self.clients: del self.clients[addr]
                if addr in self.active_streams:
                    self.gui_app.after(0, self.active_streams[addr].destroy)
                    del self.active_streams[addr]
                ui_callback()
                break

    def send_command(self, addr, command_dict):
        with self.lock:
            if addr in self.clients:
                try:
                    client_sock, _ = self.clients[addr]
                    payload = (json.dumps(command_dict) + "\n").encode("utf-8")
                    client_sock.sendall(payload)
                except socket.error:
                    pass

    def broadcast_command(self, command_dict):
        with self.lock:
            for addr in list(self.clients.keys()):
                try:
                    client_sock, _ = self.clients[addr]
                    payload = (json.dumps(command_dict) + "\n").encode("utf-8")
                    client_sock.sendall(payload)
                except socket.error:
                    pass
