# main.py
from src.app import ViseeonyxApp


def main():
    app = ViseeonyxApp(False)  # False => don't redirect stdout/stderr
    app.MainLoop()


if __name__ == "__main__":
    main()
