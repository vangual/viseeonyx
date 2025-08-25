# src/canvas_panel.py
import wx
import os
import json
import threading
from PIL import Image
# from PIL import ImageDraw
from .image_object import ImageObject
from .utils import snap_to_nearby_edges
from .file_navigator import FileNavigator
import logging


class CanvasPanel(wx.Panel):
    def __init__(self, parent, settings_manager):
        super().__init__(parent, style=wx.WANTS_CHARS)
        self.settings_manager = settings_manager

        self.image_objects = []
        self.selected_object = None
        self.marked_object = None

        # Initialize file navigator
        self.file_navigator = FileNavigator(settings_manager)

        # Try to avoid flickering due to redraws on-screen
        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)

        # Canvas background color (could come from settings)
        self.canvas_bg = self.settings_manager.get_setting("Canvas", "background_color", fallback="#FFFFFF")

        # Enable drag-and-drop
        self.SetDropTarget(FileDropTarget(self))

        # For drag
        self.drag_offset = None

        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

        # For resizing or panning
        self.resizing = False
        self.resizing_edge = None  # 'corner' or 'side'
        self.original_rect = None
        self.original_mouse_pos = None

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def get_selected_object(self):
        return self.selected_object

    def set_selected_object(self, obj):
        self.selected_object = obj
        # Start preloading when an object is selected
        if obj:
            self.start_preloading_for_object(obj)
        self.Refresh()

    def on_paint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.Clear()

        # Fill background
        bg_color = wx.Colour(self.canvas_bg)
        dc.SetBrush(wx.Brush(bg_color))
        dc.SetPen(wx.Pen(bg_color))
        w, h = self.GetSize()
        dc.DrawRectangle(0, 0, w, h)

        # Draw each image object
        for i, img_obj in enumerate(self.image_objects):
            try:
                img_obj.draw(dc)
                logging.debug(f"Drew image object {i}: {os.path.basename(img_obj.source_path)}")
            except Exception as e:
                logging.error(f"Failed to draw image object {i}: {e}")

        # Draw selection border if any
        if self.selected_object:
            x, y = self.selected_object.x, self.selected_object.y
            w, h = self.selected_object.width, self.selected_object.height
            dc.SetPen(wx.Pen(wx.RED, 2, style=wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRectangle(x, y, w, h)

    def on_left_down(self, event):
        mouse_x, mouse_y = event.GetPosition()
        # Check if clicked on any image object
        clicked_obj = None
        for obj in reversed(self.image_objects):  # topmost last
            if obj.contains(mouse_x, mouse_y):
                clicked_obj = obj
                break

        if clicked_obj:
            self.set_selected_object(clicked_obj)
            # Bring clicked object to the front
            self.image_objects.remove(clicked_obj)
            self.image_objects.append(clicked_obj)

            # Prepare for dragging
            self.drag_offset = (mouse_x - clicked_obj.x, mouse_y - clicked_obj.y)
        else:
            self.set_selected_object(None)
            self.drag_offset = None

        self.SetFocus()  # so we can receive key events
        event.Skip()

    def on_left_up(self, event):
        self.drag_offset = None
        self.resizing = False
        event.Skip()

    def on_mouse_move(self, event):
        if event.Dragging() and event.LeftIsDown() and self.drag_offset:
            # We are moving the selected object
            mouse_x, mouse_y = event.GetPosition()
            dx, dy = self.drag_offset
            obj = self.selected_object
            if obj:
                new_x = mouse_x - dx
                new_y = mouse_y - dy
                # Snap to edges if near
                new_x, new_y = snap_to_nearby_edges(new_x, new_y, obj.width, obj.height,
                                                    self.image_objects, self.GetSize())
                obj.x = new_x
                obj.y = new_y
                self.Refresh()
        event.Skip()

    def on_right_down(self, event):
        # If user right-clicks on an object, we'll let the main frame handle the context menu
        # (We do it in MainFrame via EVT_CONTEXT_MENU).
        # But we can also store which object was clicked:
        mouse_x, mouse_y = event.GetPosition()
        clicked_obj = None
        for obj in reversed(self.image_objects):
            if obj.contains(mouse_x, mouse_y):
                clicked_obj = obj
                break
        if clicked_obj:
            self.set_selected_object(clicked_obj)
            # bring to front
            self.image_objects.remove(clicked_obj)
            self.image_objects.append(clicked_obj)
        event.Skip()

    def on_key_down(self, event):
        # Basic key handling for zoom in/out or other hotkeys
        if not self.selected_object:
            event.Skip()
            return
        keycode = event.GetKeyCode()
        logging.debug(f"Key pressed: {keycode}")
        # e.g. + or = to zoom in, - to zoom out
        if keycode in (wx.WXK_ADD, wx.WXK_NUMPAD_ADD, 61):  # '=' can be 61
            self.selected_object.zoom_in()
            self.Refresh()
        elif keycode in (wx.WXK_SUBTRACT, wx.WXK_NUMPAD_SUBTRACT, 45):  # '-' can be 45
            self.selected_object.zoom_out()
            self.Refresh()
        elif keycode in (ord('x'), ord('X')):
            self.Close()
            os._exit(0)
        else:
            event.Skip()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel events for image navigation."""
        # Check if wheel navigation is enabled
        if not self.settings_manager.get_setting("Navigation", "enable_wheel_navigation", "true").lower() == "true":
            event.Skip()
            return

        # Must have a selected object
        if not self.selected_object:
            event.Skip()
            return

        # Get wheel rotation direction
        rotation = event.GetWheelRotation()

        if rotation > 0:
            # Wheel up - go to previous file
            self._navigate_to_adjacent_file(previous=True)
        elif rotation < 0:
            # Wheel down - go to next file
            self._navigate_to_adjacent_file(previous=False)

        event.Skip()

    def _navigate_to_adjacent_file(self, previous=False):
        """Navigate to the next or previous file in the directory."""
        if not self.selected_object:
            return

        current_path = self.selected_object.source_path

        # Get the target file
        if previous:
            target_path = self.file_navigator.get_previous_file(current_path)
        else:
            target_path = self.file_navigator.get_next_file(current_path)

        if not target_path or target_path == current_path:
            logging.debug(f"Navigation cancelled: target_path={target_path}, current_path={current_path}")
            return

        try:
            # Check if we have a preloaded image
            preloaded_image = self.file_navigator.get_preloaded_image(target_path)

            if preloaded_image:
                # Use preloaded image for instant navigation
                self.selected_object.change_source_path(target_path, preloaded_image)
                logging.debug(f"Used preloaded image for: {target_path}")
            else:
                # Load image on demand (this might cause a brief delay)
                self.selected_object.change_source_path(target_path, None)
                logging.debug(f"Loading image on demand: {target_path}")

            logging.debug(f"Navigated to: {target_path} (selected object at {self.selected_object.x}, {self.selected_object.y})")
            self.debug_image_objects()

            # Reset the image properties as if it was just dropped on canvas
            self._reset_navigated_image_properties(self.selected_object)

            # Start preloading for the new position (don't wait for it)
            preload_thread = threading.Thread(
                target=self.file_navigator.start_preloading,
                args=(target_path,),
                daemon=True
            )
            preload_thread.start()

            # Refresh the canvas immediately with forced update
            self.Refresh()
            self.Update()  # Force immediate repaint

            # Force a complete repaint cycle and invalidate the entire canvas
            wx.CallAfter(self._force_complete_repaint)

        except Exception as e:
            logging.error(f"Failed to navigate to {target_path}: {e}")

    def _force_complete_repaint(self):
        """Force a complete repaint of the canvas."""
        # Invalidate the entire client area and force immediate repaint
        self.Refresh()
        self.Update()

        # Try a different approach - manually trigger a paint event
        size = self.GetSize()
        rect = wx.Rect(0, 0, size.width, size.height)
        self.RefreshRect(rect, False)
        self.Update()

        # Also force all image objects to refresh their cached visuals
        for img_obj in self.image_objects:
            img_obj.force_refresh()

    def debug_image_objects(self):
        """Debug method to log the state of all image objects."""
        logging.debug(f"Canvas has {len(self.image_objects)} image objects:")
        for i, obj in enumerate(self.image_objects):
            logging.debug(f"  Object {i}: {obj.source_path} at ({obj.x}, {obj.y}) size ({obj.width}x{obj.height})")
            logging.debug(f"    Selected: {obj == self.selected_object}")
            logging.debug(f"    Has original: {obj._original_image is not None}")
            logging.debug(f"    Has visible: {obj._visible_image is not None}")

    def _reset_navigated_image_properties(self, image_object):
        """Reset image properties as if it was freshly dropped on canvas."""
        if not image_object:
            return

        # Store current position
        current_x, current_y = image_object.x, image_object.y

        # Set canvas size for the object
        canvas_w, canvas_h = self.GetSize()
        image_object.set_canvas_size(canvas_w, canvas_h)

        # Reset size to original (fit to canvas if needed)
        image_object.reset_size(fit_to_canvas=True)

        # Reset zoom and viewport
        image_object.reset_zoom()
        image_object.reset_viewport_offset()

        # Restore position (keep it where the user had placed the original image)
        image_object.x = current_x
        image_object.y = current_y

        # Make sure the image stays within canvas bounds
        self._ensure_image_within_canvas(image_object)

        # Force a complete refresh of the image object
        image_object.force_refresh()

    def _ensure_image_within_canvas(self, image_object):
        """Ensure the image object stays within canvas boundaries."""
        if not image_object:
            return

        canvas_w, canvas_h = self.GetSize()

        # Adjust position if image goes outside canvas
        if image_object.x + image_object.width > canvas_w:
            image_object.x = max(0, canvas_w - image_object.width)
        if image_object.y + image_object.height > canvas_h:
            image_object.y = max(0, canvas_h - image_object.height)

        # Ensure top-left corner isn't negative
        image_object.x = max(0, image_object.x)
        image_object.y = max(0, image_object.y)

    def start_preloading_for_object(self, image_object):
        """Start preloading images for the given image object."""
        if image_object and image_object.source_path:
            self.file_navigator.start_preloading(image_object.source_path)

    def on_settings_changed(self):
        """Handle settings changes - refresh caches and restart preloading."""
        # Clear caches to pick up new sort settings
        self.file_navigator.clear_cache()

        # Restart preloading for selected object if applicable
        if self.selected_object:
            self.start_preloading_for_object(self.selected_object)

    def export_to_file(self, path):
        """Composite all image objects onto a single bitmap and save to path."""
        w, h = self.GetSize()
        # Create a PIL image in memory
        background_color = self.canvas_bg if self.canvas_bg else "#FFFFFF"
        composite = Image.new("RGBA", (w, h), background_color)

        # Draw each image object
        for obj in self.image_objects:
            pil_img = obj.get_pil_cropped()
            if pil_img:
                composite.alpha_composite(pil_img, dest=(obj.x, obj.y))

        # Flatten alpha if desired (e.g. if user wants no transparency)
        # For example: composite = composite.convert("RGB")

        # Save using Pillow
        ext = os.path.splitext(path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            composite.convert("RGB").save(path, "JPEG")
        elif ext == ".png":
            composite.save(path, "PNG")
        elif ext == ".webp":
            composite.save(path, "WEBP")
        elif ext == ".bmp":
            composite.convert("RGB").save(path, "BMP")
        else:
            # default to PNG
            composite.save(path, "PNG")

    def save_canvas_state(self, path):
        """Save the list of image objects to a JSON file."""
        data = []
        for obj in self.image_objects:
            data.append({
                "source_path": obj.source_path,
                "x": obj.x,
                "y": obj.y,
                "width": obj.width,
                "height": obj.height,
                "zoom_factor": obj.zoom_factor,
                "viewport_offset": obj.viewport_offset
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_canvas_state(self, path):
        """Load the list of image objects from a JSON file."""
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.image_objects.clear()
        for item in data:
            obj = ImageObject(item["source_path"])
            obj.x = item["x"]
            obj.y = item["y"]
            obj.width = item["width"]
            obj.height = item["height"]
            obj.zoom_factor = item["zoom_factor"]
            obj.viewport_offset = tuple(item["viewport_offset"])
            self.image_objects.append(obj)
        self.selected_object = None
        self.marked_object = None
        self.Refresh()


class FileDropTarget(wx.FileDropTarget):
    """Custom drop target for image files."""
    def __init__(self, canvas_panel):
        super().__init__()
        self.canvas_panel = canvas_panel

    def OnDropFiles(self, x, y, filenames):
        c_w, c_h = self.canvas_panel.GetSize()
        # For each file, create a new image object
        for path in filenames:
            # Could validate image format if desired
            obj = ImageObject(path, canvas_width=c_w, canvas_height=c_h)
            obj.reset_size()
            obj.x, obj.y = x, y
            self.canvas_panel.image_objects.append(obj)
            # Move them slightly so they don't stack exactly
            x += 20
            y += 20

        # Start preloading for the last dropped image if it becomes selected
        if filenames:
            last_obj = self.canvas_panel.image_objects[-1]
            self.canvas_panel.start_preloading_for_object(last_obj)

        self.canvas_panel.Refresh()
        return True
