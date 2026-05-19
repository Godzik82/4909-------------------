import json
import socket
import threading

HOST = "0.0.0.0"
PORT = 5000


class TeacherServer:
    """Класс сервера для управления компьютерами студентов."""

    def __init__(self):
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.clients = {}
        self.lock = threading.Lock()

    def start_server(self, ui_callback):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        threading.Thread(
            target=self._accept_connections,
            args=(ui_callback,),
            daemon=True,
        ).start()

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
                threading.Thread(
                    target=self._listen_client,
                    args=(client_sock, addr, ui_callback),
                    daemon=True,
                ).start()
            except Exception:
                break

    def _listen_client(self, client_sock, addr, ui_callback):
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    raise ConnectionResetError
            except (ConnectionResetError, socket.error):
                with self.lock:
                    if addr in self.clients:
                        del self.clients[addr]
                ui_callback()
                break

    def send_command(self, addr, command_dict):
        with self.lock:
            if addr in self.clients:
                try:
                    client_sock = self.clients[addr][0]
                    payload = json.dumps(command_dict).encode("utf-8")
                    client_sock.sendall(payload)
                except socket.error:
                    pass

    def broadcast_command(self, command_dict):
        with self.lock:
            for addr in list(self.clients.keys()):
                try:
                    client_sock = self.clients[addr][0]
                    payload = json.dumps(command_dict).encode("utf-8")
                    client_sock.sendall(payload)
                except socket.error:
                    pass
