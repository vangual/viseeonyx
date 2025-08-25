# src/file_navigator.py
import os
import threading
from PIL import Image
import logging
from typing import List, Optional


class FileNavigator:
    """Handles file navigation and background preloading for image objects."""

    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tga'}

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self._file_cache = {}  # path -> (files_list, current_index)
        self._preload_cache = {}  # path -> PIL Image
        self._preload_threads = {}  # path -> threading.Thread
        self._lock = threading.Lock()

    def get_files_in_directory(self, file_path: str) -> tuple[List[str], int]:
        """
        Get list of image files in the same directory as file_path.
        Returns (files_list, current_index)
        """
        if not os.path.exists(file_path):
            return [], -1

        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        # Check cache first
        cache_key = directory
        if cache_key in self._file_cache:
            files_list, _ = self._file_cache[cache_key]
            try:
                current_index = files_list.index(os.path.join(directory, filename))
                return files_list, current_index
            except ValueError:
                # File not in cached list, refresh cache
                pass

        # Get all image files in directory
        try:
            all_files = os.listdir(directory)
        except (OSError, PermissionError) as e:
            logging.warning(f"Cannot read directory {directory}: {e}")
            return [], -1

        image_files = []
        for f in all_files:
            if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXTENSIONS:
                full_path = os.path.join(directory, f)
                if os.path.isfile(full_path):
                    image_files.append(full_path)

        # Sort files based on settings
        sort_method = self.settings_manager.get_setting("Navigation", "sort_method", "name_asc")
        image_files = self._sort_files(image_files, sort_method)

        # Cache the result
        self._file_cache[cache_key] = (image_files, -1)

        # Find current file index
        current_index = -1
        try:
            current_index = image_files.index(file_path)
        except ValueError:
            logging.warning(f"Current file {file_path} not found in directory listing")

        return image_files, current_index

    def _sort_files(self, files: List[str], sort_method: str) -> List[str]:
        """Sort files based on the specified method."""
        if sort_method == "name_asc":
            return sorted(files, key=lambda x: os.path.basename(x).lower())
        elif sort_method == "name_desc":
            return sorted(files, key=lambda x: os.path.basename(x).lower(), reverse=True)
        elif sort_method == "date_asc":
            return sorted(files, key=lambda x: os.path.getmtime(x))
        elif sort_method == "date_desc":
            return sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)
        else:
            logging.warning(f"Unknown sort method: {sort_method}, using name_asc")
            return sorted(files, key=lambda x: os.path.basename(x).lower())

    def get_next_file(self, current_path: str) -> Optional[str]:
        """Get the next file in the directory sequence."""
        files_list, current_index = self.get_files_in_directory(current_path)
        if not files_list or current_index == -1:
            return None

        next_index = (current_index + 1) % len(files_list)
        return files_list[next_index]

    def get_previous_file(self, current_path: str) -> Optional[str]:
        """Get the previous file in the directory sequence."""
        files_list, current_index = self.get_files_in_directory(current_path)
        if not files_list or current_index == -1:
            return None

        prev_index = (current_index - 1) % len(files_list)
        return files_list[prev_index]

    def start_preloading(self, current_path: str):
        """Start background preloading of adjacent images."""
        if not self.settings_manager.get_setting("Navigation", "enable_wheel_navigation", "true").lower() == "true":
            return

        preload_count = int(self.settings_manager.get_setting("Navigation", "preload_count", "2"))
        if preload_count <= 0:
            return

        files_list, current_index = self.get_files_in_directory(current_path)
        if not files_list or current_index == -1:
            return

        # Limit preload count to reasonable bounds to avoid loading entire folder
        max_preload = min(preload_count, 5, len(files_list) // 2)

        # Determine which files to preload
        files_to_preload = set()  # Use set to avoid duplicates
        for i in range(1, max_preload + 1):
            # Next files
            next_idx = (current_index + i) % len(files_list)
            if files_list[next_idx] != current_path:  # Don't preload current file
                files_to_preload.add(files_list[next_idx])

            # Previous files
            prev_idx = (current_index - i) % len(files_list)
            if files_list[prev_idx] != current_path:  # Don't preload current file
                files_to_preload.add(files_list[prev_idx])

        # Start preloading threads (limit concurrent threads)
        active_threads = sum(1 for thread in self._preload_threads.values() if thread.is_alive())
        max_concurrent_threads = 3

        for file_path in files_to_preload:
            if active_threads >= max_concurrent_threads:
                break

            if file_path not in self._preload_threads or not self._preload_threads[file_path].is_alive():
                thread = threading.Thread(target=self._preload_image, args=(file_path,), daemon=True)
                self._preload_threads[file_path] = thread
                thread.start()
                active_threads += 1

    def _preload_image(self, file_path: str):
        """Preload an image in the background."""
        try:
            with self._lock:
                if file_path in self._preload_cache:
                    return  # Already preloaded

            # Load the image
            img = Image.open(file_path)

            with self._lock:
                self._preload_cache[file_path] = img
                logging.debug(f"Preloaded image: {file_path}")

        except Exception as e:
            logging.warning(f"Failed to preload image {file_path}: {e}")

    def get_preloaded_image(self, file_path: str) -> Optional[Image.Image]:
        """Get a copy of preloaded image if available."""
        with self._lock:
            cached_image = self._preload_cache.get(file_path)
            if cached_image:
                # Return a copy to avoid sharing the same PIL Image instance
                # between multiple ImageObject instances
                try:
                    return cached_image.copy()
                except Exception as e:
                    logging.warning(f"Failed to copy preloaded image {file_path}: {e}")
                    return None
            return None

    def clear_cache(self):
        """Clear all caches."""
        with self._lock:
            self._file_cache.clear()
            self._preload_cache.clear()

        # Stop all preloading threads
        for thread in self._preload_threads.values():
            if thread.is_alive():
                thread.join(timeout=0.1)  # Don't wait too long
        self._preload_threads.clear()

    def invalidate_directory_cache(self, directory: str):
        """Invalidate cache for a specific directory."""
        with self._lock:
            if directory in self._file_cache:
                del self._file_cache[directory]
