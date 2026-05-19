import base64
import io
import json
import os
import socket
import threading
import time
from PIL import ImageGrab
from pynput import keyboard, mouse

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


class StudentClient:
    """Класс клиента для выполнения директив администратора и стрима экрана."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.frozen = False
        self.mouse_listener = None
        self.kb_listener = None
        self.root = None
        self.streaming = False  # Флаг активной Live-трансляции

        # Контроллеры для виртуальной симуляции ввода (удаленное управление)
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()

    def connect_to_teacher(self):
        threading.Thread(target=self._connection_loop, daemon=True).start()

    def _connection_loop(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((SERVER_IP, SERVER_PORT))
                username = os.getlogin()
                self.socket.sendall((json.dumps({"username": username}) + "\n").encode("utf-8"))

                if self.root:
                    self.root.lbl_status.config(text="Подключено к кабинету", fg="#000000")

                self._receive_commands()
            except socket.error:
                print("Сервер не найден. Реконнект через 3 сек...")
                if self.root:
                    self.root.lbl_status.config(text="Ожидание сервера преподавателя...", fg="#666666")
                time.sleep(3)

    def _receive_commands(self):
        buffer = ""
        while True:
            try:
                data = self.socket.recv(1024 * 64).decode("utf-8")
                if not data: raise ConnectionResetError
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip(): continue
                    self._handle_action(json.loads(line))
            except Exception:
                self.streaming = False
                if self.root:
                    self.root.lbl_status.config(text="Ошибка: Связь разорвана. Переподключение...", fg="#FF0000")
                break

    def _handle_action(self, cmd):
        action = cmd.get("action")

        if action == "message":
            if self.root: self.root.after(0, self.root.show_custom_message, cmd.get("text"))
        elif action == "freeze":
            self.toggle_freeze(cmd.get("state", False))
        elif action == "exam":
            if self.root: self.root.after(0, self.root.start_exam_mode, cmd.get("duration", 60))
        elif action == "disconnect":
            if self.root: self.root.after(0, self.root.destroy)
        
        # Запуск и остановка циклического стрима экрана
        elif action == "start_stream":
            if not self.streaming:
                self.streaming = True
                threading.Thread(target=self._live_stream_loop, daemon=True).start()
        elif action == "stop_stream":
            self.streaming = False

        # Обработка удаленного управления от преподавателя
        elif action == "remote_input":
            self._execute_remote_input(cmd)

    def _live_stream_loop(self):
        """Бесконечный цикл захвата экрана, отрисовки курсора и отправки кадров."""
        from PIL import ImageDraw
        
        was_frozen = self.frozen
        if was_frozen: 
            self.toggle_freeze(False)

        while self.streaming:
            try:
                # 1. Захватываем чистый экран
                screenshot = ImageGrab.grab()
                
                # 2. Получаем текущую координату системного курсора мыши студента
                mx, my = self.mouse_controller.position
                
                # 3. Рисуем курсор прямо на изображении
                draw = ImageDraw.Draw(screenshot)
                # Рисуем указатель в виде полигона (треугольника) контрастного цвета
                cursor_points = [(mx, my), (mx + 10, my + 15), (mx + 4, my + 18)]
                draw.polygon(cursor_points, fill="white", outline="black")
                
                # 4. Сжимаем и кодируем кадр
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format="JPEG", quality=35)
                img_bytes = img_byte_arr.getvalue()
                
                base64_string = base64.b64encode(img_bytes).decode("utf-8")
                payload = {"action": "screenshot_data", "image": base64_string}
                
                self.socket.sendall((json.dumps(payload) + "\n").encode("utf-8"))
                time.sleep(0.1)  # Ограничение ~10 FPS для плавной работы сети
            except Exception:
                break
        
        if was_frozen and self.streaming is False:
            self.toggle_freeze(True)


    def _execute_remote_input(self, cmd):
        """Эмуляция команд ввода на физическом уровне ОС студента."""
        try:
            itype = cmd.get("type")
            
            if itype == "mouse_move":
                # Получаем разрешение экрана студента
                screen_w, screen_h = ImageGrab.grab().size
                # Переводим относительные координаты преподавателя в пиксели студента
                target_x = int(cmd.get("rx") * screen_w)
                target_y = int(cmd.get("ry") * screen_h)
                self.mouse_controller.position = (target_x, target_y)

            elif itype == "mouse_click":
                button_num = cmd.get("button")
                state = cmd.get("state")
                btn = mouse.Button.left if button_num == 1 else mouse.Button.right
                
                if state == "press":
                    self.mouse_controller.press(btn)
                else:
                    self.mouse_controller.release(btn)

            elif itype == "key":
                char = cmd.get("char")
                keysym = cmd.get("keysym")
                if char:
                    self.keyboard_controller.type(char)
                elif keysym == "BackSpace":
                    self.keyboard_controller.press(keyboard.Key.backspace)
                    self.keyboard_controller.release(keyboard.Key.backspace)
        except Exception as e:
            print(f"Ошибка эмуляции ввода: {e}")

    def toggle_freeze(self, state):
        if state and not self.frozen:
            self.frozen = True
            self.mouse_listener = mouse.Listener(suppress=True)
            self.kb_listener = keyboard.Listener(suppress=True)
            self.mouse_listener.start()
            self.kb_listener.start()
        elif not state and self.frozen:
            self.frozen = False
            if self.mouse_listener: self.mouse_listener.stop()
            if self.kb_listener: self.kb_listener.stop()
