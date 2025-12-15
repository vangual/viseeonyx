# src/image_object.py
import wx
import logging
from PIL import Image
from .utils import bytes_to_human_readable


class ImageObject:
    def __init__(self, source_path, canvas_width=None, canvas_height=None):
        self.source_path = source_path
        self.x = 0
        self.y = 0
        self.width = 200  # default
        self.height = 150  # default
        self.zoom_factor = 1.0
        self.viewport_offset = (0, 0)  # top-left corner within the image

        # Cache the original PIL image (lazy load)
        self._original_image = None
        self._aspect_ratio = None
        self._visible_image = None  # cached visible portion
        self._last_dc = None  # for redraw functionality

        # Status overlay system for user feedback
        self.status_message = None  # Text to show in overlay
        self.status_type = None  # 'info', 'warning', 'processing'
        self.show_status_overlay = False

        if canvas_width and canvas_height:
            self.canvas_w = canvas_width
            self.canvas_h = canvas_height
        else:
            self.canvas_w = None
            self.canvas_h = None

    def load_image(self):
        if not self._original_image:
            # Always load fresh to ensure complete isolation between objects
            try:
                self._original_image = Image.open(self.source_path)
                # Immediately create a copy to ensure complete isolation
                self._original_image = self._original_image.copy()
                w, h = self._original_image.size
                self._aspect_ratio = w / float(h) if h != 0 else 1.0
            except Exception as e:
                logging.error(f"Failed to load image {self.source_path}: {e}")
                self._original_image = None
                self._aspect_ratio = 1.0

    def change_source_path(self, new_path, preloaded_image=None):
        """Change the source path and optionally use a preloaded image."""
        if new_path == self.source_path:
            return  # No change needed

        self.source_path = new_path

        # Use preloaded image if available, otherwise clear cache
        if preloaded_image:
            # Make sure we have a completely independent copy
            try:
                self._original_image = preloaded_image.copy()
                w, h = self._original_image.size
                self._aspect_ratio = w / float(h) if h != 0 else 1.0
            except Exception as e:
                logging.error(f"Failed to copy preloaded image for {new_path}: {e}")
                self._original_image = None
                self._aspect_ratio = None
        else:
            self._original_image = None
            self._aspect_ratio = None

        # Clear all cached images to force reload/redraw
        self._visible_image = None

        # Invalidate any cached display context
        self._last_dc = None

    def draw(self, dc):
        """Draw the visible portion of this image onto the given DC."""
        self._last_dc = dc  # Store for redraw functionality
        self.load_image()
        if not self._original_image:
            return

        # Compute the visible region
        # For simplicity, we just scale the entire image by zoom_factor,
        # then crop according to viewport_offset & the object's width/height.
        scaled_w = int(self._original_image.width * self.zoom_factor)
        scaled_h = int(self._original_image.height * self.zoom_factor)

        # Convert PIL to wx.Bitmap
        # Create a working copy to ensure complete isolation
        pil_scaled = self._original_image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        # Crop out the portion that fits in our object rectangle
        vx, vy = self.viewport_offset
        # Ensure we don't go out of bounds
        right = min(vx + self.width, scaled_w)
        bottom = min(vy + self.height, scaled_h)

        # Create a new cropped image for this specific draw operation
        try:
            cropped = pil_scaled.crop((vx, vy, right, bottom))
            # Store as _visible_image but make it a copy to prevent sharing issues
            self._visible_image = cropped.copy()
        except Exception as e:
            logging.error(f"Error cropping image {self.source_path}: {e}")
            return

        wx_img = wx.Image(cropped.size[0], cropped.size[1])
        wx_img.SetData(cropped.convert("RGB").tobytes())
        if cropped.mode == "RGBA":
            wx_img.SetAlpha(cropped.getchannel("A").tobytes())

        bmp = wx.Bitmap(wx_img)
        dc.DrawBitmap(bmp, self.x, self.y, True)
        self._last_dc = dc

        # Draw status overlay if needed
        if self.show_status_overlay and self.status_message:
            self._draw_status_overlay(dc)

    def contains(self, mx, my):
        """Check if the mouse point (mx,my) is inside this object's bounding box."""
        return (self.x <= mx <= self.x + self.width) and (self.y <= my <= self.y + self.height)

    def zoom_in(self):
        """Zoom in by 25% (up to 500%)."""
        new_zoom = self.zoom_factor * 1.25
        if new_zoom <= 5.0:
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            self._update_dimensions_for_zoom(old_zoom, new_zoom)
            self._clear_image_caches()

            # Show zoom level feedback
            zoom_percent = int(self.zoom_factor * 100)
            self.set_status_overlay(f"Zoom: {zoom_percent}%", 'info')
            # Auto-clear after a short delay would be handled by the canvas
        else:
            # Show limit reached message
            self.set_status_overlay("Max zoom reached (500%)", 'warning')

    def zoom_out(self):
        """Zoom out by 25% (down to 25%)."""
        new_zoom = self.zoom_factor * 0.8
        if new_zoom >= 0.25:
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            self._update_dimensions_for_zoom(old_zoom, new_zoom)
            self._clear_image_caches()

            # Show zoom level feedback
            zoom_percent = int(self.zoom_factor * 100)
            self.set_status_overlay(f"Zoom: {zoom_percent}%", 'info')
            # Auto-clear after a short delay would be handled by the canvas
        else:
            # Show limit reached message
            self.set_status_overlay("Min zoom reached (25%)", 'warning')

    def _update_dimensions_for_zoom(self, old_zoom, new_zoom):
        """Update object dimensions when zoom changes."""
        if not self._original_image:
            self.load_image()

        if self._original_image:
            # Calculate the new display size based on zoom
            base_width = self._original_image.width
            base_height = self._original_image.height

            # Update width and height to reflect the zoomed size
            self.width = max(1, int(base_width * new_zoom))
            self.height = max(1, int(base_height * new_zoom))

            # Adjust viewport offset to try to keep the same center point visible
            if old_zoom != 0:
                zoom_ratio = new_zoom / old_zoom
                center_x = self.viewport_offset[0] + (self.width / zoom_ratio) // 2
                center_y = self.viewport_offset[1] + (self.height / zoom_ratio) // 2

                new_vx = max(0, int(center_x - self.width // 2))
                new_vy = max(0, int(center_y - self.height // 2))

                # Ensure viewport doesn't exceed scaled image bounds
                max_vx = max(0, int(base_width * new_zoom) - self.width)
                max_vy = max(0, int(base_height * new_zoom) - self.height)

                self.viewport_offset = (min(new_vx, max_vx), min(new_vy, max_vy))

    def _clear_image_caches(self):
        """Clear cached images to force refresh on next draw."""
        self._visible_image = None

    def set_status_overlay(self, message, status_type='info'):
        """Set a status overlay message to display on the image object.

        Args:
            message: Text to display (None to hide overlay)
            status_type: 'info', 'warning', 'processing'
        """
        self.status_message = message
        self.status_type = status_type
        self.show_status_overlay = message is not None

    def clear_status_overlay(self):
        """Clear the status overlay."""
        self.status_message = None
        self.status_type = None
        self.show_status_overlay = False

    def _draw_status_overlay(self, dc):
        """Draw a status overlay on the image object."""
        if not self.status_message:
            return

        # Set up drawing parameters based on status type
        if self.status_type == 'processing':
            bg_color = wx.Colour(255, 165, 0, 180)  # Orange with transparency
            text_color = wx.Colour(0, 0, 0)
        elif self.status_type == 'warning':
            bg_color = wx.Colour(255, 69, 0, 180)  # Red-orange with transparency
            text_color = wx.Colour(255, 255, 255)
        else:  # 'info' or default
            bg_color = wx.Colour(70, 130, 180, 180)  # Steel blue with transparency
            text_color = wx.Colour(255, 255, 255)

        # Calculate overlay position and size
        overlay_padding = 8
        text_size = dc.GetTextExtent(self.status_message)

        overlay_width = text_size.width + (overlay_padding * 2)
        overlay_height = text_size.height + (overlay_padding * 2)

        # Center the overlay on the image object
        overlay_x = self.x + (self.width - overlay_width) // 2
        overlay_y = self.y + (self.height - overlay_height) // 2

        # Ensure overlay stays within image bounds
        overlay_x = max(self.x, min(overlay_x, self.x + self.width - overlay_width))
        overlay_y = max(self.y, min(overlay_y, self.y + self.height - overlay_height))

        # Draw semi-transparent background
        dc.SetBrush(wx.Brush(bg_color))
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, 100)))
        dc.DrawRoundedRectangle(overlay_x, overlay_y, overlay_width, overlay_height, 4)

        # Draw text
        dc.SetTextForeground(text_color)
        text_x = overlay_x + overlay_padding
        text_y = overlay_y + overlay_padding
        dc.DrawText(self.status_message, text_x, text_y)

    def get_pil_cropped(self):
        """Return a PIL image of the object as it appears (cropped and scaled)."""
        self.load_image()
        if not self._original_image:
            return None
        scaled_w = int(self._original_image.width * self.zoom_factor)
        scaled_h = int(self._original_image.height * self.zoom_factor)
        pil_scaled = self._original_image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        vx, vy = self.viewport_offset
        right = min(vx + self.width, scaled_w)
        bottom = min(vy + self.height, scaled_h)
        if right <= vx or bottom <= vy:
            return None
        cropped = pil_scaled.crop((vx, vy, right, bottom))

        # Create a new RGBA image for consistent alpha usage
        if cropped.mode != "RGBA":
            cropped = cropped.convert("RGBA")
        # The top-left corner in the final composite is (self.x, self.y).
        # We'll just return the cropped image; the calling code places it.
        self._visible_image = cropped
        return cropped

    def set_canvas_size(self, canvas_width, canvas_height):
        self.canvas_w = canvas_width
        self.canvas_h = canvas_height

    def reset_size(self, fit_to_canvas=True):
        """Reset the image size to its original dimensions."""
        self.load_image()
        if not self._original_image:
            return

        # Reset width and height to original dimensions
        self.width = self._original_image.width
        self.height = self._original_image.height

        if fit_to_canvas:
            # Fit to canvas and adjust placement on that axis
            if self.width > self.canvas_w:
                self.width = self.canvas_w
                self.x = 0
            if self.height > self.canvas_h:
                self.height = self.canvas_h
                self.y = 0

    def reset_zoom(self):
        """Reset the zoom factor to 1.0."""
        old_zoom = self.zoom_factor
        self.zoom_factor = 1.0
        self._update_dimensions_for_zoom(old_zoom, 1.0)
        self._clear_image_caches()

        # Show feedback
        self.set_status_overlay("Zoom reset to 100%", 'info')

    def reset_viewport_offset(self):
        """Reset the viewport offset to (0, 0)."""
        self.viewport_offset = (0, 0)

    def redraw(self):
        """Redraw the image in its current position and size."""
        if hasattr(self, '_last_dc') and self._last_dc:
            self.draw(self._last_dc)

    def force_refresh(self):
        """Force a complete refresh of the image object by clearing all caches."""
        self._visible_image = None
        self._last_dc = None

    def __eq__(self, value):
        if not isinstance(value, ImageObject):
            return False
        return self.source_path == value.source_path

    def __repr__(self):
        # Calculate memory usage for PIL Images
        if self._original_image:
            # PIL Images: width * height * number of channels * bytes per channel
            orig_mem = self._original_image.width * self._original_image.height * len(self._original_image.getbands())
            mem_orig = bytes_to_human_readable(orig_mem)
        else:
            mem_orig = "0 B"

        if self._visible_image:
            vis_mem = self._visible_image.width * self._visible_image.height * len(self._visible_image.getbands())
            mem_vis = bytes_to_human_readable(vis_mem)
        else:
            mem_vis = "0 B"

        return (
            f"ImageObject({self.source_path}, x={self.x}, y={self.y}, "
            f"w={self.width}, h={self.height}, "
            f"mem_orig={mem_orig}, "
            f"mem_vis={mem_vis})"
        )
