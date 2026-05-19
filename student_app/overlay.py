import ctypes
import tkinter as tk
from message_window import MessageWindow


class StudentOverlay(tk.Tk):
    """Главное окно клиента для отображения статусов и таймера."""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.client.root = self
        self.title("Студент")
        self.geometry("300x180")
        self.configure(bg="#FFFFFF")

        self.lbl_status = tk.Label(
            self,
            text="Установка соединения...",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#666666",
        )
        self.lbl_status.pack(expand=True, pady=(15, 0))

        self.lbl_timer = tk.Label(
            self, text="", font=("Arial", 24), bg="#FFFFFF", fg="#FF0000"
        )

        self.btn_exit = tk.Button(
            self,
            text="Выйти",
            font=("Arial", 10),
            bg="#000000",
            fg="#FFFFFF",
            activebackground="#333333",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            command=self.quit_application,
        )
        self.btn_exit.pack(fill=tk.X, padx=20, pady=20)

        # 1. Программный перехват Alt+F4 и закрытия
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        # 2. НИЗКОУРОВНЕВОЕ ОТКЛЮЧЕНИЕ КРЕСТИКА (Делает его серым/неактивным в Windows)
        self.after(10, self._disable_close_button)

        self.client.connect_to_teacher()

    def _disable_close_button(self):
        """Обращение к WinAPI для деактивации системной кнопки закрытия."""
        try:
            # Получаем дескриптор (HWND) окна Tkinter
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # Получаем системное меню этого окна
            sys_menu = ctypes.windll.user32.GetSystemMenu(hwnd, False)
            if sys_menu:
                # SC_CLOSE = 0xF060, MF_BYCOMMAND = 0x00000000, MF_GRAYED = 0x00000001
                # Отключаем и закрашиваем пункт «Закрыть» (вместе с крестиком)
                ctypes.windll.user32.EnableMenuItem(sys_menu, 0xF060, 0x00000001)
        except Exception as e:
            print(f"Не удалось деактивировать крестик: {e}")

    def show_custom_message(self, text):
        """Создание и отображение нового окна сообщения."""
        MessageWindow(self, text)

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
