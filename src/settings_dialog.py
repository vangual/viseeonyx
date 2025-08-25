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

        # Create a notebook for tabbed settings
        notebook = wx.Notebook(panel)

        # Canvas settings tab
        canvas_panel = wx.Panel(notebook)
        canvas_sizer = wx.BoxSizer(wx.VERTICAL)

        # Example setting: canvas background color
        bg_color_label = wx.StaticText(canvas_panel,
                                       label="Canvas Background Color (HTML hex):")
        self.bg_color_text = wx.TextCtrl(canvas_panel,
                                         value=self.settings_manager.get_setting("Canvas",
                                                                                 "background_color",
                                                                                 "#FFFFFF"))
        canvas_sizer.Add(bg_color_label, 0, wx.ALL, 5)
        canvas_sizer.Add(self.bg_color_text, 0, wx.ALL | wx.EXPAND, 5)
        canvas_panel.SetSizer(canvas_sizer)

        # Navigation settings tab
        nav_panel = wx.Panel(notebook)
        nav_sizer = wx.BoxSizer(wx.VERTICAL)

        # Enable mouse wheel navigation
        self.enable_wheel_nav = wx.CheckBox(nav_panel, label="Enable Mouse Wheel Navigation")
        enable_nav = self.settings_manager.get_setting("Navigation", "enable_wheel_navigation", "true")
        self.enable_wheel_nav.SetValue(enable_nav.lower() == "true")
        nav_sizer.Add(self.enable_wheel_nav, 0, wx.ALL, 5)

        # Sort method
        sort_label = wx.StaticText(nav_panel, label="File Sorting Method:")
        self.sort_choice = wx.Choice(nav_panel, choices=[
            "Name (A-Z)", "Name (Z-A)", "Date Modified (Oldest First)", "Date Modified (Newest First)"
        ])
        sort_method = self.settings_manager.get_setting("Navigation", "sort_method", "name_asc")
        sort_index = {"name_asc": 0, "name_desc": 1, "date_asc": 2, "date_desc": 3}.get(sort_method, 0)
        self.sort_choice.SetSelection(sort_index)

        nav_sizer.Add(sort_label, 0, wx.ALL, 5)
        nav_sizer.Add(self.sort_choice, 0, wx.ALL | wx.EXPAND, 5)

        # Preload count
        preload_label = wx.StaticText(nav_panel, label="Number of Images to Preload (in each direction):")
        self.preload_spin = wx.SpinCtrl(nav_panel, value=self.settings_manager.get_setting("Navigation", "preload_count", "2"),
                                        min=0, max=5)  # Reduced max from 10 to 5 to prevent excessive preloading
        nav_sizer.Add(preload_label, 0, wx.ALL, 5)
        nav_sizer.Add(self.preload_spin, 0, wx.ALL, 5)

        # Navigation instructions
        help_text = wx.StaticText(nav_panel,
                                  label="Mouse wheel navigation allows you to browse through images in the same folder as the selected image.\n"
                                        "Select an image and use the mouse wheel to navigate to the next/previous file.\n"
                                        "Preloading helps improve navigation performance by loading adjacent images in the background.")
        help_text.Wrap(400)
        nav_sizer.Add(help_text, 0, wx.ALL, 5)

        nav_panel.SetSizer(nav_sizer)

        # Add tabs to notebook
        notebook.AddPage(canvas_panel, "Canvas")
        notebook.AddPage(nav_panel, "Navigation")

        panel_sizer.Add(notebook, 1, wx.EXPAND)
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

        # Save navigation settings
        self.settings_manager.set_setting("Navigation", "enable_wheel_navigation",
                                          "true" if self.enable_wheel_nav.GetValue() else "false")

        sort_methods = ["name_asc", "name_desc", "date_asc", "date_desc"]
        selected_sort = sort_methods[self.sort_choice.GetSelection()]
        self.settings_manager.set_setting("Navigation", "sort_method", selected_sort)

        self.settings_manager.set_setting("Navigation", "preload_count", str(self.preload_spin.GetValue()))

        self.settings_manager.save()
        self.EndModal(wx.ID_OK)
