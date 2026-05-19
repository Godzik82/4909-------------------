import tkinter as tk


class StudentOverlay(tk.Tk):
    """Окно клиента для отображения статусов и таймера экзамена."""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.client.root = self
        self.title("Студент")
        self.geometry("300x180")  # Увеличили высоту под кнопку выхода
        self.configure(bg="#FFFFFF")

        self.lbl_status = tk.Label(
            self,
            text="Установка соединения...",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#666666",
        )
        self.lbl_status.pack(expand=True, pady=(10, 0))

        self.lbl_timer = tk.Label(
            self, text="", font=("Arial", 24), bg="#FFFFFF", fg="#FF0000"
        )

        # # НОВАЯ КНОПКА: Выход из приложения студента
        # self.btn_exit = tk.Button(
        #     self,
        #     text="Выйти",
        #     font=("Arial", 10),
        #     bg="#000000",
        #     fg="#FFFFFF",
        #     activebackground="#333333",
        #     activeforeground="#FFFFFF",
        #     relief=tk.FLAT,
        #     command=self.quit_application,
        # )
        # self.btn_exit.pack(fill=tk.X, padx=20, pady=15)

        self.client.connect_to_teacher()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

    def start_exam_mode(self, duration):
        """Перевод интерфейса в режим экзамена с таймером."""
        self.lbl_status.config(text="ИДЕТ ЭКЗАМЕН", fg="#000000")
        self.lbl_timer.pack(expand=True)
        self._countdown(duration)

    def _countdown(self, remaining):
        """Рекурсивный отсчет времени экзамена."""
        if remaining <= 0:
            self.lbl_timer.config(text="ВРЕМЯ ИСТЕКЛО")
            self.client.toggle_freeze(True)
            return

        mins, secs = divmod(remaining, 60)
        self.lbl_timer.config(text=f"{mins:02d}:{secs:02d}")
        self.after(1000, self._countdown, remaining - 1)

    def quit_application(self):
        """Безопасный выход с принудительной разблокировкой ввода."""
        self.client.toggle_freeze(False)
        self.destroy()
