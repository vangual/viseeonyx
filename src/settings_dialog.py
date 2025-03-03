# src/settings_dialog.py
import wx


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings_manager):
        super().__init__(parent, title="Settings",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.settings_manager = settings_manager

        # Top-level sizer for the dialog
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Create a panel to hold the settings controls
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # Example setting: canvas background color
        bg_color_label = wx.StaticText(panel,
                                       label="Canvas Background Color (HTML hex):")
        self.bg_color_text = wx.TextCtrl(panel,
                                         value=self.settings_manager.get_setting("Canvas",
                                                                                 "background_color",
                                                                                 "#FFFFFF"))
        panel_sizer.Add(bg_color_label, 0, wx.ALL, 5)
        panel_sizer.Add(self.bg_color_text, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(panel_sizer)

        # Add the panel to the dialog's sizer
        sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 10)

        # Create the button sizer (buttons will have the dialog as parent)
        btn_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)

    def on_ok(self, event):
        # Save the new background color setting
        new_bg = self.bg_color_text.GetValue().strip()
        self.settings_manager.set_setting("Canvas", "background_color", new_bg)
        self.settings_manager.save()
        self.EndModal(wx.ID_OK)
