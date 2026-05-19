from client import StudentClient
from overlay import StudentOverlay


def main():
    """Основная функция для инициализации и запуска клиента."""
    client_instance = StudentClient()
    app = StudentOverlay(client_instance)
    app.mainloop()


if __name__ == "__main__":
    main()
