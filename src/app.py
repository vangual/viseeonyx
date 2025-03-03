# src/app.py
import wx
from .main_frame import MainFrame
from .settings_manager import SettingsManager
# import os
import logging


class ViseeonyxApp(wx.App):
    def OnInit(self):
        """
        Called upon app initialization. Creates the main frame and shows it.
        """

        # Initialize logging logging to stdout
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Viseeonyx started")

        # Initialize settings manager (loads .ini, sets defaults, etc.)
        self.settings_manager = SettingsManager()

        # Create main frame
        self.frame = MainFrame(None, title="viseeonyx",
                               settings_manager=self.settings_manager)
        self.SetTopWindow(self.frame)

        # By default, show in fullscreen (no OS window decorations)
        self.frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)

        self.frame.Show()
        return True
