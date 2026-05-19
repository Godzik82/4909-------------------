import os
import sys

# Динамически добавляем путь к текущей папке в системные пути поиска Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui import TeacherApp
from server import TeacherServer


def main():
    """Основная функция для инициализации и запуска сервера."""
    server = TeacherServer()
    app = TeacherApp(server)
    app.mainloop()


if __name__ == "__main__":
    main()
