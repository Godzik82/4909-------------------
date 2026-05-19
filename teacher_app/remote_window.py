import base64
import io
import tkinter as tk
from PIL import Image, ImageTk


class RemoteControlWindow(tk.Toplevel):
    """Интерактивное окно для Live-трансляции и удаленного управления."""

    def __init__(self, parent, addr, username, server):
        super().__init__(parent)
        self.addr = addr
        self.username = username
        self.server = server
        
        # Флаг, разрешено ли управление в данный момент
        self.control_enabled = True
        
        self.title(f"Управление ПК: {username} ({addr})")
        self.geometry("800x650")
        self.configure(bg="#121212")

        # Верхняя панель для кнопки управления
        top_bar = tk.Frame(self, bg="#1E1E1E", height=40)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        top_bar.pack_propagate(False)

        # Чёрно-белая кнопка переключения режима управления
        self.btn_toggle = tk.Button(
            top_bar,
            text="Управление: ВКЛ",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF",
            fg="#000000",
            activebackground="#CCCCCC",
            activeforeground="#000000",
            relief=tk.FLAT,
            command=self._toggle_control
        )
        self.btn_toggle.pack(side=tk.LEFT, padx=10, pady=5)

        # Контейнер для вывода кадров трансляции
        self.img_label = tk.Label(self, bg="#121212")
        self.img_label.pack(fill=tk.BOTH, expand=True)

        # Привязка событий мыши и клавиатуры
        self.img_label.bind("<Motion>", self._on_mouse_move)
        self.img_label.bind("<ButtonPress>", self._on_mouse_click)
        self.img_label.bind("<ButtonRelease>", self._on_mouse_release)
        self.bind("<KeyPress>", self._on_key_press)

        # Запрашиваем старт стрима у студента
        self.server.send_command(self.addr, {"action": "start_stream"})
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _toggle_control(self):
        """Включение и отключение отправки команд управления."""
        self.control_enabled = not self.control_enabled
        if self.control_enabled:
            self.btn_toggle.config(
                text="Управление: ВКЛ", bg="#FFFFFF", fg="#000000"
            )
        else:
            self.btn_toggle.config(
                text="Управление: ВЫКЛ (Только просмотр)", 
                bg="#333333", 
                fg="#FFFFFF"
            )

    def update_frame(self, base64_string):
        """Обновление кадра в реальном времени."""
        try:
            img_bytes = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(img_bytes))
            
            width = max(self.winfo_width(), 100)
            height = max(self.winfo_height(), 100) - 40
            image.thumbnail((width, height))
            
            render = ImageTk.PhotoImage(image)
            self.img_label.config(image=render)
            self.img_label.image = render
        except Exception as e:
            print(f"Ошибка обновления кадра: {e}")

    def _on_mouse_move(self, event):
        if not self.control_enabled:
            return
        lbl_w = max(self.img_label.winfo_width(), 1)
        lbl_h = max(self.img_label.winfo_height(), 1)
        cmd = {
            "action": "remote_input",
            "type": "mouse_move",
            "rx": event.x / lbl_w,
            "ry": event.y / lbl_h
        }
        self.server.send_command(self.addr, cmd)

    def _on_mouse_click(self, event):
        if not self.control_enabled:
            return
        cmd = {
            "action": "remote_input", 
            "type": "mouse_click", 
            "button": event.num, 
            "state": "press"
        }
        self.server.send_command(self.addr, cmd)

    def _on_mouse_release(self, event):
        if not self.control_enabled:
            return
        cmd = {
            "action": "remote_input", 
            "type": "mouse_click", 
            "button": event.num, 
            "state": "release"
        }
        self.server.send_command(self.addr, cmd)

    def _on_key_press(self, event):
        if not self.control_enabled:
            return
        cmd = {
            "action": "remote_input", 
            "type": "key", 
            "char": event.char, 
            "keysym": event.keysym
        }
        self.server.send_command(self.addr, cmd)

    def _on_close(self):
        self.server.send_command(self.addr, {"action": "stop_stream"})
        if self.addr in self.server.active_streams:
            del self.server.active_streams[self.addr]
        self.destroy()
