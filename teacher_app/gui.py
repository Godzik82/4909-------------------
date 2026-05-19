import io
import struct
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
from PIL import Image, ImageTk


class TeacherApp(tk.Tk):
    """Графический интерфейс преподавателя (Черно-белый стиль)."""

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.title("Панель Преподавателя (Администратор)")
        self.geometry("750x530")  # Слегка увеличили высоту для новой кнопки
        self.configure(bg="#121212")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "TLabel", background="#121212", foreground="#FFFFFF"
        )
        self.style.configure(
            "TButton",
            background="#FFFFFF",
            foreground="#000000",
            borderwidth=1,
        )
        self.style.map("TButton", background=[("active", "#CCCCCC")])

        self._create_widgets()
        self.server.start_server(self.update_client_list)

    def _create_widgets(self):
        left_frame = tk.Frame(self, bg="#121212")
        left_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10
        )

        lbl = ttk.Label(
            left_frame, text="Подключенные студенты:", font=("Arial", 12)
        )
        lbl.pack(anchor=tk.W, pady=5)

        self.client_box = tk.Listbox(
            left_frame,
            bg="#1E1E1E",
            fg="#FFFFFF",
            selectbackground="#FFFFFF",
            selectforeground="#000000",
            font=("Arial", 11),
        )
        self.client_box.pack(fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(self, bg="#1E1E1E", width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        btn_screenshot = ttk.Button(
            right_frame, text="Просмотр экрана", command=self.view_screenshot
        )
        btn_screenshot.pack(fill=tk.X, pady=5, padx=10)

        btn_msg = ttk.Button(
            right_frame, text="Отправить сообщение", command=self.send_msg
        )
        btn_msg.pack(fill=tk.X, pady=5, padx=10)

        btn_freeze = ttk.Button(
            right_frame, text="Заморозить ПК", command=self.freeze_pcs
        )
        btn_freeze.pack(fill=tk.X, pady=5, padx=10)

        btn_unfreeze = ttk.Button(
            right_frame, text="Разморозить ПК", command=self.unfreeze_pcs
        )
        btn_unfreeze.pack(fill=tk.X, pady=5, padx=10)

        btn_exam = ttk.Button(
            right_frame, text="Запустить экзамен", command=self.start_exam
        )
        btn_exam.pack(fill=tk.X, pady=5, padx=10)

        btn_disconnect = ttk.Button(
            right_frame, text="Отключить ПК", command=self.disconnect_client
        )
        btn_disconnect.pack(fill=tk.X, pady=5, padx=10)

        # НОВАЯ КНОПКА: Выход из приложения преподавателя
        btn_exit = ttk.Button(
            right_frame, text="Выйти", command=self.quit_application
        )
        btn_exit.pack(fill=tk.X, pady=20, padx=10)

    def update_client_list(self):
        self.client_box.delete(0, tk.END)
        with self.server.lock:
            for addr, (_, name) in self.server.clients.items():
                self.client_box.insert(tk.END, f"{name} ({addr}:{addr})")

    def _get_selected_addr(self):
        try:
            index = self.client_box.curselection()
            with self.server.lock:
                return list(self.server.clients.keys())[index]
        except IndexError:
            return None

    def view_screenshot(self):
        addr = self._get_selected_addr()
        if not addr:
            messagebox.showwarning("Внимание", "Выберите студента из списка!")
            return

        cmd = {"action": "screenshot"}
        self.server.send_command(addr, cmd)
        threading.Thread(
            target=self._receive_image_stream, args=(addr,), daemon=True
        ).start()

    def _receive_image_stream(self, addr):
        try:
            with self.server.lock:
                if addr not in self.server.clients:
                    return
                client_sock = self.server.clients[addr]

            raw_size = client_sock.recv(4)
            if not raw_size:
                return
            img_size = struct.unpack(">I", raw_size)[0]

            data = b""
            while len(data) < img_size:
                packet = client_sock.recv(img_size - len(data))
                if not packet:
                    return
                data += packet

            self.after(0, self._show_screenshot_window, data)
        except Exception as e:
            print(f"Ошибка получения скриншота: {e}")

    def _show_screenshot_window(self, img_bytes):
        screen_win = tk.Toplevel(self)
        screen_win.title("Просмотр экрана студента")
        screen_win.configure(bg="#121212")

        image = Image.open(io.BytesIO(img_bytes))
        image.thumbnail((800, 600))
        render = ImageTk.PhotoImage(image)

        img_label = tk.Label(screen_win, image=render, bg="#121212")
        img_label.image = render
        img_label.pack(padx=10, pady=10)

    def send_msg(self):
        msg = simpledialog.askstring("Сообщение", "Введите текст:")
        if msg:
            addr = self._get_selected_addr()
            cmd = {"action": "message", "text": msg}
            if addr:
                self.server.send_command(addr, cmd)
            else:
                self.server.broadcast_command(cmd)

    def freeze_pcs(self):
        addr = self._get_selected_addr()
        cmd = {"action": "freeze", "state": True}
        if addr:
            self.server.send_command(addr, cmd)
        else:
            self.server.broadcast_command(cmd)

    def unfreeze_pcs(self):
        addr = self._get_selected_addr()
        cmd = {"action": "freeze", "state": False}
        if addr:
            self.server.send_command(addr, cmd)
        else:
            self.server.broadcast_command(cmd)

    def start_exam(self):
        minutes = simpledialog.askinteger(
            "Экзамен", "Время экзамена (минут):", minvalue=1, maxvalue=180
        )
        if minutes:
            cmd = {"action": "exam", "duration": minutes * 60}
            self.server.broadcast_command(cmd)

    def disconnect_client(self):
        addr = self._get_selected_addr()
        if addr:
            self.server.send_command(addr, {"action": "disconnect"})

    def quit_application(self):
        """Корректное закрытие приложения администратора."""
        self.destroy()
