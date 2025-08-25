# src/settings_manager.py
import os
import configparser


class SettingsManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.loaded_path = None
        self.default_file_name = "viseeonyx_settings.ini"

        # Attempt to load from local folder first, else from user config folder
        if os.path.exists(self.default_file_name):
            self.loaded_path = self.default_file_name
        else:
            # E.g., use an OS-specific path. For simplicity, let's just try local only:
            pass

        if self.loaded_path:
            self.config.read(self.loaded_path)
        else:
            # We have no existing .ini; use defaults
            pass

        # Ensure sections exist
        if not self.config.has_section("Canvas"):
            self.config.add_section("Canvas")
            self.config.set("Canvas", "background_color", "#FFFFFF")

        # Navigation settings
        if not self.config.has_section("Navigation"):
            self.config.add_section("Navigation")
            self.config.set("Navigation", "sort_method", "name_asc")  # name_asc, name_desc, date_asc, date_desc
            self.config.set("Navigation", "preload_count", "1")  # Number of images to preload in each direction
            self.config.set("Navigation", "enable_wheel_navigation", "true")

    def get_setting(self, section, key, fallback=None):
        if self.config.has_option(section, key):
            return self.config.get(section, key)
        return fallback

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save(self):
        """Save current settings to disk."""
        if not self.loaded_path:
            self.loaded_path = self.default_file_name
        with open(self.loaded_path, "w", encoding="utf-8") as f:
            self.config.write(f)
