import tkinter as tk


class MessageWindow(tk.Toplevel):
    """Кастомное независимое окно для отображения сообщений от учителя."""

    def __init__(self, parent, text):
        super().__init__(parent)
        self.title("Уведомление от преподавателя")
        self.geometry("350x200")
        self.configure(bg="#121212")
        self.resizable(False, False)

        # Окно всегда поверх остальных программ
        self.attributes("-topmost", True)

        # Текст сообщения
        lbl_msg = tk.Label(
            self,
            text=text,
            font=("Arial", 11),
            bg="#121212",
            fg="#FFFFFF",
            wraplength=310,
            justify=tk.CENTER,
        )
        lbl_msg.pack(expand=True, padx=20, pady=(20, 10))

        # Контрастная белая кнопка ОК
        btn_ok = tk.Button(
            self,
            text="ОК",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF",
            fg="#000000",
            activebackground="#CCCCCC",
            activeforeground="#000000",
            relief=tk.FLAT,
            width=10,
            command=self.destroy,
        )
        btn_ok.pack(pady=(0, 20))
