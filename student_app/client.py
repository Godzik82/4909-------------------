import io
import json
import os
import socket
import struct
import threading
from tkinter import messagebox
from PIL import ImageGrab
from pynput import keyboard, mouse

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


class StudentClient:
    """Класс клиента для выполнения директив администратора."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.frozen = False
        self.mouse_listener = None
        self.kb_listener = None
        self.root = None

    def connect_to_teacher(self):
        """Установление связи с сервером преподавателя."""
        try:
            self.socket.connect((SERVER_IP, SERVER_PORT))
            username = os.getlogin()
            identity = {"username": username}
            self.socket.sendall(json.dumps(identity).encode("utf-8"))

            if self.root:
                self.root.lbl_status.config(
                    text="Подключено к кабинету", fg="#000000"
                )

            threading.Thread(
                target=self._receive_commands, daemon=True
            ).start()
        except socket.error:
            print("Не удалось подключиться к серверу преподавателя.")
            if self.root:
                self.root.lbl_status.config(
                    text="Ошибка: Сервер недоступен", fg="#FF0000"
                )

    def _receive_commands(self):
        """Поток обработки входящих сетевых JSON-пакетов."""
        while True:
            try:
                data = self.socket.recv(4096).decode("utf-8")
                if not data:
                    break
                command = json.loads(data)
                self._handle_action(command)
            except Exception:
                break

    def _handle_action(self, cmd):
        """Маршрутизация команд в зависимости от действия."""
        action = cmd.get("action")

        if action == "message":
            text = cmd.get("text")
            threading.Thread(
                target=lambda: messagebox.showinfo(
                    "Преподаватель", text
                ),
                daemon=True,
            ).start()

        elif action == "freeze":
            state = cmd.get("state", False)
            self.toggle_freeze(state)

        elif action == "exam":
            duration = cmd.get("duration", 60)
            if self.root:
                self.root.after(0, self.root.start_exam_mode, duration)

        elif action == "disconnect":
            if self.root:
                self.root.after(0, self.root.destroy)

        elif action == "screenshot":
            self._send_screenshot()

    def _send_screenshot(self):
        """Снятие скриншота экрана и передача байтов серверу."""
        try:
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format="JPEG", quality=70)
            img_bytes = img_byte_arr.getvalue()

            header = struct.pack(">I", len(img_bytes))
            self.socket.sendall(header + img_bytes)
        except Exception as e:
            print(f"Ошибка отправки экрана: {e}")

    def toggle_freeze(self, state):
        """Включение или выключение блокировки ввода (заморозка)."""
        if state and not self.frozen:
            self.frozen = True
            self.mouse_listener = mouse.Listener(suppress=True)
            self.kb_listener = keyboard.Listener(suppress=True)
            self.mouse_listener.start()
            self.kb_listener.start()
        elif not state and self.frozen:
            self.frozen = False
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.kb_listener:
                self.kb_listener.stop()
