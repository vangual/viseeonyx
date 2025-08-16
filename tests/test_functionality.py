import unittest
import os
import tempfile
import json
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.arrangement import arrange_no_resize, arrange_with_resize  # noqa: E402
from src.settings_manager import SettingsManager  # noqa: E402


class TestArrangement(unittest.TestCase):
    def setUp(self):
        """Set up mock image objects for testing."""
        class MockImageObject:
            def __init__(self, width=100, height=100):
                self.x = 0
                self.y = 0
                self.width = width
                self.height = height
                self._aspect_ratio = width / height if height != 0 else 1.0

            def load_image(self):
                """Mock load_image method."""
                pass

            def set_canvas_size(self, canvas_w, canvas_h):
                """Mock set_canvas_size method."""
                self.canvas_w = canvas_w
                self.canvas_h = canvas_h

        self.objects = [
            MockImageObject(50, 50),
            MockImageObject(75, 60),
            MockImageObject(100, 80)
        ]
        self.canvas_size = (800, 600)

    def test_arrange_no_resize(self):
        """Test that arrange_no_resize positions objects without changing size."""
        original_sizes = [(obj.width, obj.height) for obj in self.objects]

        arrange_no_resize(self.objects, self.canvas_size)

        # Check that sizes haven't changed
        for i, obj in enumerate(self.objects):
            self.assertEqual((obj.width, obj.height), original_sizes[i])

        # Check that objects are positioned (not all at 0,0)
        positions = [(obj.x, obj.y) for obj in self.objects]
        unique_positions = set(positions)
        self.assertGreater(len(unique_positions), 1, "Objects should be positioned differently")

    def test_arrange_with_resize(self):
        """Test that arrange_with_resize changes object dimensions."""
        original_sizes = [(obj.width, obj.height) for obj in self.objects]

        arrange_with_resize(self.objects, self.canvas_size)

        # At least some objects should have different sizes
        new_sizes = [(obj.width, obj.height) for obj in self.objects]
        self.assertNotEqual(original_sizes, new_sizes, "Sizes should change with resize arrangement")

        # All objects should fit within canvas bounds
        for obj in self.objects:
            self.assertLessEqual(obj.x + obj.width, self.canvas_size[0])
            self.assertLessEqual(obj.y + obj.height, self.canvas_size[1])

    def test_empty_object_list(self):
        """Test that arrangement functions handle empty object lists gracefully."""
        empty_objects = []

        # Should not raise exceptions
        arrange_no_resize(empty_objects, self.canvas_size)
        arrange_with_resize(empty_objects, self.canvas_size)

        self.assertEqual(len(empty_objects), 0)


class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for settings testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_settings_manager_defaults(self):
        """Test that SettingsManager provides expected defaults."""
        manager = SettingsManager()

        # Should have default canvas background color
        bg_color = manager.get_setting("Canvas", "background_color", "#000000")
        self.assertEqual(bg_color, "#FFFFFF")  # Default should be white

    def test_settings_persistence(self):
        """Test that settings can be saved and loaded."""
        manager = SettingsManager()

        # Set a custom value
        manager.set_setting("Test", "key", "value")
        manager.save()

        # Create new manager instance (simulates restart)
        manager2 = SettingsManager()
        value = manager2.get_setting("Test", "key", "default")

        self.assertEqual(value, "value")

    def test_fallback_values(self):
        """Test that fallback values work when settings don't exist."""
        manager = SettingsManager()

        value = manager.get_setting("NonExistent", "key", "fallback")
        self.assertEqual(value, "fallback")


class TestCanvasStateManagement(unittest.TestCase):
    def setUp(self):
        """Set up temporary files for state testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_canvas_state_format(self):
        """Test that canvas state has expected JSON structure."""
        # Create a mock canvas state
        mock_state = [
            {
                "source_path": "/path/to/image1.png",
                "x": 10,
                "y": 20,
                "width": 100,
                "height": 50,
                "zoom_factor": 1.5,
                "viewport_offset": [0, 0]
            },
            {
                "source_path": "/path/to/image2.png",
                "x": 150,
                "y": 80,
                "width": 200,
                "height": 100,
                "zoom_factor": 1.0,
                "viewport_offset": [10, 5]
            }
        ]

        # Save state to file
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(mock_state, f, indent=2)

        # Load and verify structure
        with open(self.state_file, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)

        self.assertEqual(len(loaded_state), 2)

        # Check required fields
        required_fields = ["source_path", "x", "y", "width", "height", "zoom_factor", "viewport_offset"]
        for obj_data in loaded_state:
            for field in required_fields:
                self.assertIn(field, obj_data, f"Field '{field}' should be present in state data")


if __name__ == '__main__':
    unittest.main()
