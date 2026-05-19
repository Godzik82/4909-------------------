from gui import TeacherApp
from server import TeacherServer


def main():
    server = TeacherServer()
    app = TeacherApp(server)
    app.mainloop()


if __name__ == "__main__":
    main()
