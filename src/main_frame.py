# src/main_frame.py
import wx
from .canvas_panel import CanvasPanel
from .settings_dialog import SettingsDialog
from .arrangement import arrange_no_resize, arrange_with_resize
import os
import logging


class MainFrame(wx.Frame):
    def __init__(self, parent, title, settings_manager, debug_mode=False):
        # Choose style based on debug mode
        if debug_mode:
            # Use default window style for debug mode (with title bar, borders, etc.)
            style = wx.DEFAULT_FRAME_STYLE
        else:
            # Style for borderless fullscreen mode
            style = wx.FRAME_NO_TASKBAR | wx.NO_BORDER

        super().__init__(parent, title=title, style=style)

        self.settings_manager = settings_manager
        self.debug_mode = debug_mode

        # Create the main panel (the canvas)
        self.canvas_panel = CanvasPanel(self, settings_manager=self.settings_manager)

        # Bind a context menu event on the frame level
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        # Also allow the user to exit fullscreen with ESC or F11
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        # A simple sizer so that the canvas fills the entire frame
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # Make sure we can handle sizing events
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        """Handle resize events to refresh the layout if needed."""
        self.canvas_panel.Refresh()
        event.Skip()

    def on_right_click(self, event):
        """Show a context menu for the entire canvas if user right-clicked outside any image object."""
        menu = wx.Menu()

        # If there's a selected image object, show relevant items
        sel_obj = self.canvas_panel.get_selected_object()
        if sel_obj:
            mark_item = menu.Append(wx.ID_ANY, "Mark This Object")
            self.Bind(wx.EVT_MENU, self.on_mark_object, mark_item)

            swap_item = menu.Append(wx.ID_ANY, "Swap With Marked Object")
            self.Bind(wx.EVT_MENU, self.on_swap_objects, swap_item)

            menu.AppendSeparator()

            reset_size_item = menu.Append(wx.ID_ANY, "Reset Size to Original")
            self.Bind(wx.EVT_MENU, sel_obj.reset_size, reset_size_item)
            reset_zoom_item = menu.Append(wx.ID_ANY, "Reset Zoom to Original")
            self.Bind(wx.EVT_MENU, sel_obj.reset_zoom, reset_zoom_item)
            reset_viewport_offset_item = menu.Append(wx.ID_ANY, "Reset Offset to Original")
            self.Bind(wx.EVT_MENU, sel_obj.reset_viewport_offset, reset_viewport_offset_item)

            menu.AppendSeparator()

            delete_item = menu.Append(wx.ID_ANY, "Delete Selected Object")
            self.Bind(wx.EVT_MENU, self.on_delete_object, delete_item)
        else:
            # No object selected, or user clicked on empty canvas
            pass

        menu.AppendSeparator()

        arrange_item = menu.Append(wx.ID_ANY, "Arrange All (No Resize)")
        self.Bind(wx.EVT_MENU, self.on_arrange_no_resize, arrange_item)

        arrange_resize_item = menu.Append(wx.ID_ANY, "Arrange All (With Resize)")
        self.Bind(wx.EVT_MENU, self.on_arrange_with_resize, arrange_resize_item)

        menu.AppendSeparator()

        export_item = menu.Append(wx.ID_ANY, "Export Canvas...")
        self.Bind(wx.EVT_MENU, self.on_export_canvas, export_item)

        menu.AppendSeparator()

        load_state_item = menu.Append(wx.ID_ANY, "Load Canvas State...")
        self.Bind(wx.EVT_MENU, self.on_load_canvas_state, load_state_item)
        save_state_item = menu.Append(wx.ID_ANY, "Save Canvas State...")
        self.Bind(wx.EVT_MENU, self.on_save_canvas_state, save_state_item)

        menu.AppendSeparator()

        settings_item = menu.Append(wx.ID_ANY, "Settings...")
        self.Bind(wx.EVT_MENU, self.on_open_settings, settings_item)

        quit_item = menu.Append(wx.ID_ANY, "Quit")
        self.Bind(wx.EVT_MENU, self.on_quit, quit_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_mark_object(self, event):
        """Mark the currently selected object."""
        sel_obj = self.canvas_panel.get_selected_object()
        if sel_obj:
            self.canvas_panel.marked_object = sel_obj

    def on_swap_objects(self, event):
        """Swap selected object with previously marked object."""
        sel_obj = self.canvas_panel.get_selected_object()
        marked_obj = self.canvas_panel.marked_object
        if sel_obj and marked_obj and sel_obj != marked_obj:
            # Swap positions & sizes
            sel_obj.x, marked_obj.x = marked_obj.x, sel_obj.x
            sel_obj.y, marked_obj.y = marked_obj.y, sel_obj.y
            sel_obj.width, marked_obj.width = marked_obj.width, sel_obj.width
            sel_obj.height, marked_obj.height = marked_obj.height, sel_obj.height
            sel_obj.viewport_offset, marked_obj.viewport_offset = marked_obj.viewport_offset, sel_obj.viewport_offset
            sel_obj.zoom_factor, marked_obj.zoom_factor = marked_obj.zoom_factor, sel_obj.zoom_factor
            self.canvas_panel.Refresh()

    def on_delete_object(self, event):
        sel_obj = self.canvas_panel.get_selected_object()
        if sel_obj:
            self.canvas_panel.image_objects.remove(sel_obj)
            self.canvas_panel.selected_object = None
            self.canvas_panel.Refresh()

    def on_arrange_no_resize(self, event):
        if wx.MessageBox("Arrange all images without resizing?\nThis will move them around on the canvas.",
                         "Confirm Arrangement", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            arrange_no_resize(self.canvas_panel.image_objects, self.GetSize())
            self.canvas_panel.Refresh()

    def on_arrange_with_resize(self, event):
        if wx.MessageBox("Arrange all images WITH resizing?\nThis will move and resize them to fit.",
                         "Confirm Arrangement", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            arrange_with_resize(self.canvas_panel.image_objects, self.GetSize())
            self.canvas_panel.Refresh()

    def on_export_canvas(self, event):
        """Export the current canvas as an image file."""
        wildcard = "PNG files (*.png)|*.png|" \
                   "JPEG files (*.jpg)|*.jpg|" \
                   "WebP files (*.webp)|*.webp|" \
                   "BMP files (*.bmp)|*.bmp"
        dialog = wx.FileDialog(self, "Save Exported Image", wildcard=wildcard,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.canvas_panel.export_to_file(path)
        dialog.Destroy()

    def on_load_canvas_state(self, event):
        """Load canvas state from JSON."""
        dialog = wx.FileDialog(self, "Load Canvas State", wildcard="JSON files (*.json)|*.json",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.canvas_panel.load_canvas_state(path)
        dialog.Destroy()

    def on_save_canvas_state(self, event):
        """Save canvas state to JSON."""
        dialog = wx.FileDialog(self, "Save Canvas State", wildcard="JSON files (*.json)|*.json",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.canvas_panel.save_canvas_state(path)
        dialog.Destroy()

    def on_open_settings(self, event):
        dlg = SettingsDialog(self, self.settings_manager)
        dlg.ShowModal()
        dlg.Destroy()
        # Potentially apply new settings here, e.g. canvas background color
        self.canvas_panel.Refresh()

    def on_quit(self, event):
        # End fullscreen, or close the app entirely
        self.Close()
        os._exit(0)  # TODO: Make this shutdown more graceful

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        logging.debug(f"Key pressed: {keycode}")
        # ESC or F11 to exit fullscreen
        if keycode in (wx.WXK_ESCAPE, wx.WXK_F11):
            self.on_quit(None)
        # on key "x", run the on_quit function
        elif keycode in (ord('x'), ord('X')):
            self.on_quit(None)
        else:
            event.Skip()
