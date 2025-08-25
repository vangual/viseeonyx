# Mouse Wheel Navigation Feature Demo

## Overview
This document demonstrates the new mouse wheel navigation feature in Viseeonyx, which allows users to browse through all images in a folder using the mouse wheel.

## How to Test the Feature

### 1. Prepare Test Images
- Create a folder with several image files (JPG, PNG, GIF, etc.)
- Make sure the images have different names or modification dates for testing sorting

### 2. Launch Viseeonyx
```bash
uv run python main.py
```

### 3. Load an Image
- Drag and drop one of your test images onto the canvas
- The image will appear and be automatically selected (red border)

### 4. Test Mouse Wheel Navigation
- With the image selected, use your mouse wheel:
  - **Wheel up**: Navigate to previous image in the folder
  - **Wheel down**: Navigate to next image in the folder
- The selected image should change to show different files from the same folder
- Navigation wraps around (last → first, first → last)

### 5. Test Settings
- Right-click to open context menu → "Settings..."
- Go to the "Navigation" tab
- Try different sorting methods:
  - Name (A-Z) / Name (Z-A)
  - Date Modified (Oldest First) / Date Modified (Newest First)
- Adjust preload count (higher = more responsive, more memory usage)
- Enable/disable the feature entirely

### 6. Test Performance
- Use a folder with many images (10+)
- Notice smooth navigation due to background preloading
- Check that navigation works immediately after changing sort settings

## Expected Behavior

### Navigation
- Mouse wheel only works when an image is selected
- Files are sorted according to the setting (default: Name A-Z)
- Navigation wraps around at folder boundaries
- Only image files are included (JPG, PNG, GIF, BMP, WebP, TIFF, TGA)
- **Each navigated image resets to its original size and properties** (behaves like a fresh drop)
- **Position is preserved** when navigating between images

### Performance
- **Limited preloading**: Only 2 adjacent images (configurable up to 5) preloaded by default
- **Responsive navigation**: Instant response when preloaded images are available
- **Smart threading**: Maximum 3 concurrent preload threads to avoid system overload
- Subsequent navigation should be very responsive (preloaded)
- Settings changes clear cache and restart preloading

### Error Handling
- If file cannot be loaded, navigation skips to next available file
- Missing files or permission errors are logged but don't crash the application
- Works with folders containing non-image files (ignores them)

## Integration with Existing Features
- Selected image maintains its position, zoom, and other properties when navigating
- All other Viseeonyx features work normally with navigated images
- Can export, arrange, save state, etc. with any navigated image
- Multiple images can be on canvas, wheel only affects selected one
- **Multiple instances of same image**: Can have multiple copies of the same image file on canvas simultaneously
- **Immediate visual updates**: Navigation changes are visible immediately without requiring clicks or drags

## Troubleshooting
- If navigation seems slow, reduce preload count in settings (default is now 2)
- If navigation doesn't work, check that "Enable Mouse Wheel Navigation" is checked
- If files appear in wrong order, check the sort method setting
- If images don't reset properly, they should now behave like freshly dropped images
- **Fixed**: Multiple instances of the same image can now coexist on canvas without disappearing
- **Fixed**: Visual updates now happen immediately during wheel navigation
- Memory usage is now more controlled with limited preloading (max 5 images per direction)
