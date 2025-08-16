# debug_main.py - Debug version that doesn't start in fullscreen
import sys
import os
import wx
import logging

sys.path.insert(0, os.path.dirname(__file__))

from src.main_frame import MainFrame  # noqa: E402
from src.settings_manager import SettingsManager  # noqa: E402


class DebugViseeonyxApp(wx.App):
    def OnInit(self):
        """
        Debug version of the app that starts in windowed mode instead of fullscreen.
        """
        # Initialize logging logging to stdout
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Viseeonyx started in DEBUG mode (windowed)")

        # Initialize settings manager (loads .ini, sets defaults, etc.)
        self.settings_manager = SettingsManager()

        # Create main frame
        self.frame = MainFrame(None, title="viseeonyx (DEBUG)",
                               settings_manager=self.settings_manager, debug_mode=True)
        self.SetTopWindow(self.frame)

        # Start in windowed mode for debugging - easier to see and interact with
        self.frame.SetSize((1200, 800))  # Set a reasonable window size
        self.frame.Center()  # Center on screen
        self.frame.Show(True)

        # Force the window to front and focus
        self.frame.Raise()
        self.frame.RequestUserAttention()

        logging.info("Debug window should now be visible")
        return True


def main():
    app = DebugViseeonyxApp(False)  # False => don't redirect stdout/stderr
    app.MainLoop()


if __name__ == "__main__":
    main()
