# main.py
import sys
from src.app import ViseeonyxApp


def main():
    app = ViseeonyxApp(False)  # False => don't redirect stdout/stderr
    app.MainLoop()
    # Exit with the code set by the application
    sys.exit(app.exit_code)


if __name__ == "__main__":
    main()
