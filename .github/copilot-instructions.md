# Viseeonyx AI Coding Agent Instructions

## Project Overview
Viseeonyx is a wxPython-based collage creation tool that runs in fullscreen mode. Users drag & drop images to create arrangements, with real-time manipulation capabilities.

## Architecture & Key Components

### Core Structure
- **`src/app.py`**: Main application entry with `ViseeonyxApp` - initializes settings, creates main frame, starts in fullscreen
- **`src/main_frame.py`**: Main window container with context menu system and event routing
- **`src/canvas_panel.py`**: Primary workspace - handles image objects, drag/drop, mouse interactions, export/import
- **`src/image_object.py`**: Individual image representation with PIL backend, zoom/viewport/positioning logic
- **`src/arrangement.py`**: Auto-layout algorithms (`arrange_no_resize`, `arrange_with_resize`)
- **`src/settings_manager.py`**: INI-based configuration with fallback defaults
- **`src/file_navigator.py`**: File discovery, sorting, and background preloading for mouse wheel navigation

### Key Patterns & Conventions

#### Image Object Management
- Images are `ImageObject` instances with position (`x`, `y`), dimensions (`width`, `height`), `zoom_factor`, and `viewport_offset`
- PIL images cached lazily in `_original_image` field, converted to wx.Bitmap for rendering
- Each object can be cropped/zoomed independently - viewport shows portion of scaled source image
- **Mouse Wheel Navigation**: Objects can change source path dynamically with `change_source_path()` method
- **Background Preloading**: `FileNavigator` preloads adjacent images for smooth navigation experience
- **Image Isolation**: Preloaded images are copied to prevent conflicts between multiple objects showing same file
- **Immediate Refresh**: Visual updates use `Refresh()`, `Update()`, and `wx.SafeYield()` for immediate display

#### Event Flow
- Right-click → context menu with object-specific actions (mark/swap, reset size/zoom/offset, delete)
- Left-click → select/drag with `snap_to_nearby_edges()` utility for alignment assistance
- Mouse wheel → navigate through files in same folder (when object selected)
- Keyboard: `+`/`-` for zoom, `X` or `Esc` to quit, hotkeys handled at multiple levels

#### State Management & Export
- Canvas state serialized to JSON with image paths and transformations
- Settings stored in `viseeonyx_settings.ini` (local directory preferred)
- **Canvas Export**: `CanvasPanel.export_to_file()` composites all image objects into single output image using PIL
- Export formats: PNG (with alpha), JPEG, WebP, BMP - PIL handles format conversion automatically
- No undo/redo system - operations are immediate and persistent

#### Fullscreen UI Philosophy
- No traditional menus/toolbars - all actions via right-click context menus
- Double-buffered canvas to prevent flicker during drag operations
- `wx.FRAME_NO_TASKBAR | wx.NO_BORDER` style with `ShowFullScreen(True, wx.FULLSCREEN_ALL)`

## Development Patterns

### Development Workflow with `uv`
- **Setup**: `uv sync` to install dependencies from `uv.lock`
- **Run application**: `uv run python main.py`
- **Run tests**: `uv run python run_tests.py`
- **Add dependencies**: `uv add <package>` (updates `pyproject.toml` and `uv.lock`)
- **Virtual environment**: Managed automatically by `uv` - no manual venv creation needed

### Adding New Features
- Image manipulation: Extend `ImageObject` methods, ensure viewport/zoom interaction works correctly
- UI actions: Add context menu items in `MainFrame.on_right_click()`, implement handler methods
- Canvas operations: Extend `CanvasPanel` with new mouse/keyboard event handlers
- File operations: Follow export/import pattern using PIL for image processing, JSON for state

### Export Functionality
- **Primary Use Case**: Export entire collage as single image file combining all positioned/sized objects
- `export_to_file()` creates PIL composite with canvas background, alpha-composites each object at its position
- Handles format conversion (PNG preserves alpha, JPEG/BMP flattens to RGB)
- Export triggered via right-click context menu → "Export Canvas..."

### Testing & Debugging
- Logging configured in `app.py` - use `logging.debug()` for development traces
- **Test Framework**: Basic unittest suite in `tests/` directory - run with `uv run python run_tests.py`
- Core tests: `test_core.py` (ImageObject, utils), `test_functionality.py` (arrangement, settings)
- Manual testing workflow via drag/drop and context menus for UI components
- Run with `uv run python main.py` - dependencies managed via `uv` (see `uv.lock`)
- **Debug Mode**: App auto-detects debugger and shows windowed (with title bar) instead of fullscreen for easier debugging

### Planned Features (Not Yet Implemented)
- **Extensible Settings System**: Global settings window with plugin support and search functionality
- **Cross-Platform Packaging**: Single executable builds for Windows, macOS, and Linux
- **Expanded Testing Suite**: GUI component tests and integration tests to complement existing unit tests

### Memory Management
- Images loaded on-demand in `load_image()`, cached until object destruction
- `_visible_image` cache for currently rendered portion
- Use `bytes_to_human_readable()` utility for memory usage display in `__repr__`

### Common Gotchas
- Canvas size changes require calling `set_canvas_size()` on image objects
- PIL/wxPython image conversion requires careful RGBA/RGB mode handling
- Mouse event coordinates are canvas-relative, not screen-relative
- Drag operations require `SetFocus()` to receive keyboard events properly
- **wxPython Debug Visibility**: App automatically switches to windowed mode with title bar when debugger detected (vs fullscreen in production)

## Dependencies & Environment
- Python 3.12+ required
- **Uses `uv` for dependency management** (see `uv.lock`) - install dependencies with `uv sync`
- Primary dependencies: `wxPython`, `Pillow`
- Settings file created in working directory, not user config folder
- **Development workflow**: Use `uv run` prefix for Python commands (e.g., `uv run python main.py`)
