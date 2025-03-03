# src/image_object.py
import wx
from PIL import Image


class ImageObject:
    def __init__(self, source_path):
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

    def load_image(self):
        if not self._original_image:
            self._original_image = Image.open(self.source_path)
            w, h = self._original_image.size
            self._aspect_ratio = w / float(h) if h != 0 else 1.0

    def draw(self, dc):
        """Draw the visible portion of this image onto the given DC."""
        self.load_image()
        if not self._original_image:
            return

        # Compute the visible region
        # For simplicity, we just scale the entire image by zoom_factor,
        # then crop according to viewport_offset & the object's width/height.
        scaled_w = int(self._original_image.width * self.zoom_factor)
        scaled_h = int(self._original_image.height * self.zoom_factor)

        # Convert PIL to wx.Bitmap
        pil_scaled = self._original_image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        # Crop out the portion that fits in our object rectangle
        vx, vy = self.viewport_offset
        # Ensure we don't go out of bounds
        right = min(vx + self.width, scaled_w)
        bottom = min(vy + self.height, scaled_h)
        cropped = pil_scaled.crop((vx, vy, right, bottom))

        wx_img = wx.Image(cropped.size[0], cropped.size[1])
        wx_img.SetData(cropped.convert("RGB").tobytes())
        if cropped.mode == "RGBA":
            wx_img.SetAlpha(cropped.getchannel("A").tobytes())

        bmp = wx.Bitmap(wx_img)
        dc.DrawBitmap(bmp, self.x, self.y, True)

    def contains(self, mx, my):
        """Check if the mouse point (mx,my) is inside this object's bounding box."""
        return (self.x <= mx <= self.x + self.width) and (self.y <= my <= self.y + self.height)

    def zoom_in(self):
        """Zoom in by 25% (up to 500%)."""
        new_zoom = self.zoom_factor * 1.25
        if new_zoom <= 5.0:
            self.zoom_factor = new_zoom

    def zoom_out(self):
        """Zoom out by 25% (down to 25%)."""
        new_zoom = self.zoom_factor * 0.8
        if new_zoom >= 0.25:
            self.zoom_factor = new_zoom

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
        return cropped
