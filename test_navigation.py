#!/usr/bin/env python3
"""
Test script to debug the mouse wheel navigation issues.
This creates a simple test scenario to isolate the problems.
"""

import os
import tempfile
import sys
import logging
from PIL import Image
import wx

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.canvas_panel import CanvasPanel  # noqa: E402
from src.settings_manager import SettingsManager  # noqa: E402

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Navigation Test", size=(800, 600))

        # Create settings manager
        self.settings_manager = SettingsManager()

        # Create canvas
        self.canvas = CanvasPanel(self, self.settings_manager)

        # Create test images in temp directory
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_images()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # Add test images to canvas
        self.add_test_images()

        self.Center()

    def create_test_images(self):
        """Create test images with different colors."""
        colors = ['red', 'green', 'blue', 'yellow', 'purple']
        self.test_files = []

        for i, color in enumerate(colors):
            # Create a simple colored image
            img = Image.new('RGB', (200, 200), color)
            filename = f"test_{color}_{i + 1}.png"
            filepath = os.path.join(self.temp_dir, filename)
            img.save(filepath)
            self.test_files.append(filepath)
            logging.info(f"Created test image: {filepath}")

    def add_test_images(self):
        """Add the first test image twice to test duplicate handling."""
        # Add first image at position (50, 50)
        from src.image_object import ImageObject

        obj1 = ImageObject(self.test_files[0])
        obj1.x = 50
        obj1.y = 50
        obj1.set_canvas_size(*self.canvas.GetSize())
        obj1.reset_size()
        self.canvas.image_objects.append(obj1)

        # Add same image again at different position (300, 50)
        obj2 = ImageObject(self.test_files[0])
        obj2.x = 300
        obj2.y = 50
        obj2.set_canvas_size(*self.canvas.GetSize())
        obj2.reset_size()
        self.canvas.image_objects.append(obj2)

        # Select the first object
        self.canvas.set_selected_object(obj1)

        logging.info("Added two instances of the same image to canvas")
        logging.info("Test: Use mouse wheel on selected (left) image to navigate")
        logging.info("Expected: Right image should remain visible and unchanged")

    def __del__(self):
        # Clean up temp files
        if hasattr(self, 'temp_dir'):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass


class TestApp(wx.App):
    def OnInit(self):
        frame = TestFrame()
        frame.Show()
        return True


if __name__ == '__main__':
    app = TestApp()
    app.MainLoop()
