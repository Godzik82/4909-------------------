import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from remote_window import RemoteControlWindow  # Теперь Python точно найдет этот файл



class TeacherApp(tk.Tk):
    """Графический интерфейс преподавателя (Черно-белый стиль)."""

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.server.gui_app = self
        self.title("Панель Преподавателя (Администратор) - Live Stream")
        self.geometry("800x550")
        self.configure(bg="#121212")

        self.displayed_addrs = []

        self.style = ttk.Style()
        self.theme_use_setting = self.style.theme_use("clam")
        self.style.configure(
            "TLabel", background="#121212", foreground="#FFFFFF"
        )
        self.style.configure(
            "TButton", 
            background="#FFFFFF", 
            foreground="#000000", 
            borderwidth=1
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
            left_frame, 
            text="Список студентов (кликните для выбора):", 
            font=("Arial", 11)
        )
        lbl.pack(anchor=tk.W, pady=5)

        self.client_box = tk.Listbox(
            left_frame, bg="#1E1E1E", fg="#FFFFFF", 
            selectbackground="#333333", selectforeground="#FFFFFF", 
            font=("Arial", 11), selectmode=tk.MULTIPLE, 
            highlightthickness=0
        )
        self.client_box.pack(fill=tk.BOTH, expand=True)
        self.client_box.bind("<<ListboxSelect>>", self._on_select)

        right_frame = tk.Frame(self, bg="#1E1E1E", width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        btn_screenshot = ttk.Button(
            right_frame, 
            text="Управление / Live ТВ", 
            command=self.view_screenshots
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
            right_frame, text="Отключить ПК", command=self.disconnect_clients
        )
        btn_disconnect.pack(fill=tk.X, pady=5, padx=10)

        btn_exit = ttk.Button(
            right_frame, text="Выйти", command=self.quit_application
        )
        btn_exit.pack(fill=tk.X, pady=20, padx=10)

    def update_client_list(self):
        selected_indices = self.client_box.curselection()
        previously_selected_addrs = [
            self.displayed_addrs[i] 
            for i in selected_indices 
            if i < len(self.displayed_addrs)
        ]

        self.client_box.delete(0, tk.END)
        self.displayed_addrs = []

        with self.server.lock:
            for addr, (_, name) in self.server.clients.items():
                self.displayed_addrs.append(addr)
                status_box = (
                    "[X]" if addr in previously_selected_addrs else "[ ]"
                )
                self.client_box.insert(
                    tk.END, f"{status_box}  {name} ({addr}:{addr})"
                )
                if addr in previously_selected_addrs:
                    self.client_box.select_set(len(self.displayed_addrs) - 1)

    def _on_select(self, event):
        selected_indices = self.client_box.curselection()
        with self.server.lock:
            for i in range(self.client_box.size()):
                if i >= len(self.displayed_addrs): 
                    continue
                addr = self.displayed_addrs[i]
                _, name = self.server.clients.get(addr, (None, "Неизвестный"))
                if i in selected_indices:
                    self.client_box.delete(i)
                    self.client_box.insert(i, f"[X]  {name} ({addr}:{addr})")
                    self.client_box.select_set(i)
                else:
                    self.client_box.delete(i)
                    self.client_box.insert(i, f"[ ]  {name} ({addr}:{addr})")
                    self.client_box.select_clear(i)

    def _get_selected_addrs(self):
        selected_indices = self.client_box.curselection()
        return [
            self.displayed_addrs[i] 
            for i in selected_indices 
            if i < len(self.displayed_addrs)
        ]

    def view_screenshots(self):
        """Открытие интерактивных окон управления для всех выбранных ПК."""
        addrs = self._get_selected_addrs()
        if not addrs:
            messagebox.showwarning("Внимание", "Не выбрано ни одного студента!")
            return

        for addr in addrs:
            if addr in self.server.active_streams:
                continue
            
            with self.server.lock:
                _, name = self.server.clients.get(addr, (None, "Студент"))
            
            win = RemoteControlWindow(self, addr, name, self.server)
            self.server.active_streams[addr] = win

    def send_msg(self):
        msg = simpledialog.askstring("Сообщение", "Введите текст уведомления:")
        if not msg: 
            return
        addrs = self._get_selected_addrs()
        cmd = {"action": "message", "text": msg}
        if addrs:
            for addr in addrs: 
                self.server.send_command(addr, cmd)
        else:
            self.server.broadcast_command(cmd)

    def freeze_pcs(self):
        addrs = self._get_selected_addrs()
        cmd = {"action": "freeze", "state": True}
        if addrs:
            for addr in addrs: 
                self.server.send_command(addr, cmd)
        else:
            self.server.broadcast_command(cmd)

    def unfreeze_pcs(self):
        addrs = self._get_selected_addrs()
        cmd = {"action": "freeze", "state": False}
        if addrs:
            for addr in addrs: 
                self.server.send_command(addr, cmd)
        else:
            self.server.broadcast_command(cmd)

    def start_exam(self):
        minutes = simpledialog.askinteger(
            "Exam", "Время экзамена (минут):", minvalue=1, maxvalue=180
        )
        if minutes: 
            self.server.broadcast_command(
                {"action": "exam", "duration": minutes * 60}
            )

    def disconnect_clients(self):
        addrs = self._get_selected_addrs()
        if addrs:
            for addr in addrs: 
                self.server.send_command(addr, {"action": "disconnect"})
        else:
            messagebox.showwarning("Внимание", "Не выбрано ни одного студента!")

    def quit_application(self):
        try: 
            self.server.server_socket.close()
        except Exception: 
            pass
        self.destroy()
