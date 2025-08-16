# Viseeonyx

A wxPython-based collage creation tool that runs in fullscreen mode. Create beautiful image arrangements by simply dragging and dropping images, with real-time manipulation capabilities.

## Features

- **Drag & Drop Interface**: Simply drag images from your file explorer onto the canvas
- **Real-time Manipulation**: Resize, zoom, and position images with mouse interactions
- **Snap-to-Grid**: Images automatically align to nearby edges for perfect positioning
- **Multiple Export Formats**: Save your collages as PNG, JPEG, WebP, or BMP
- **State Management**: Save and load your work-in-progress collages
- **Auto-arrangement**: Automatically arrange multiple images in organized layouts
- **Fullscreen Experience**: Immersive, distraction-free creative environment

## Installation

### Requirements
- Python 3.12 or higher
- Cross-platform support (Windows, macOS, Linux)

### Quick Install
1. Clone or download this repository
2. Install dependencies using uv (recommended):
   ```bash
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application
```bash
# Using uv (recommended)
uv run python main.py

# Or using pip/regular Python
python main.py
```

The application starts in fullscreen mode for an immersive creative experience.

### Basic Operations

#### Adding Images
- **Drag & Drop**: Drag image files from your file manager directly onto the canvas
- **Supported Formats**: PNG, JPEG, GIF, BMP, and most common image formats

#### Manipulating Images
- **Select**: Left-click on any image to select it (red border appears)
- **Move**: Click and drag selected images to reposition them
- **Zoom**: Use `+` and `-` keys to zoom in/out on selected images
- **Context Menu**: Right-click for additional options

#### Context Menu Options
- **Mark/Swap Objects**: Mark an image, then swap positions with another
- **Reset Size**: Return image to original dimensions
- **Reset Zoom**: Return to 100% zoom level
- **Reset Offset**: Reset cropping/viewport position
- **Delete**: Remove selected image from canvas

#### Auto-arrangement
- **Arrange (No Resize)**: Automatically position images without changing sizes
- **Arrange (With Resize)**: Resize and position images to fit in a grid

#### Saving Your Work
- **Export Canvas**: Save the final collage as an image file (PNG, JPEG, WebP, BMP)
- **Save State**: Save the current arrangement to reload later (JSON format)
- **Load State**: Restore a previously saved arrangement

#### Keyboard Shortcuts
- **Esc** or **X**: Exit the application
- **+**: Zoom in on selected image
- **-**: Zoom out on selected image

### Tips for Best Results
- Use high-resolution images for better quality exports
- Leverage the snap-to-edge feature for precise alignment
- Save your work frequently using "Save Canvas State"
- Use the auto-arrangement features as starting points, then fine-tune manually

## Developer Documentation

### Development Setup

#### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

#### Initial Setup
```bash
# Clone the repository
git clone https://github.com/vangual/viseeonyx.git
cd viseeonyx

# Install dependencies
uv sync

# Verify installation
uv run python main.py
```

### Common Development Commands

#### Running the Application
```bash
# Production mode (fullscreen)
uv run python main.py

# Debug mode (windowed with title bar) - for development
# The app auto-detects when running in debugger/VS Code
```

#### Testing
```bash
# Run all tests
uv run python run_tests.py

# Run tests with verbose output
uv run python run_tests.py -v

# Run specific test class
uv run python run_tests.py test_core

# Alternative: using unittest directly
uv run python -m unittest discover tests -v
```

#### Dependency Management
```bash
# Install new dependency
uv add <package-name>

# Install development dependency
uv add --dev <package-name>

# Update dependencies
uv sync

# Check for outdated packages
uv pip list --outdated
```

#### VS Code Integration
The project includes VS Code configurations:
- **F5**: Debug mode (windowed)
- **Ctrl+Shift+B**: Build/run task
- **Tasks available**: Run application, sync dependencies, run tests

### Project Structure
```
viseeonyx/
├── src/                    # Main source code
│   ├── app.py             # Application entry point
│   ├── main_frame.py      # Main window and UI logic
│   ├── canvas_panel.py    # Canvas drawing and interaction
│   ├── image_object.py    # Individual image representation
│   ├── arrangement.py     # Auto-layout algorithms
│   ├── settings_manager.py # Configuration management
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── .vscode/              # VS Code configuration
├── main.py               # Application launcher
├── debug_main.py         # Debug launcher (windowed mode)
├── run_tests.py          # Test runner
└── pyproject.toml        # Project configuration
```

### Architecture Overview
- **wxPython GUI**: Cross-platform native GUI framework
- **PIL/Pillow**: Image processing and manipulation
- **Event-driven**: Mouse and keyboard interactions drive the UI
- **Component-based**: Modular design with clear separation of concerns

### Development Patterns
- **Debug Mode**: App automatically detects debugger and shows windowed interface
- **State Serialization**: JSON-based saving/loading of canvas arrangements
- **Memory Management**: Lazy image loading with caching
- **Error Handling**: Comprehensive logging throughout the application

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `uv run python run_tests.py`
6. Submit a pull request

### Building for Distribution
*Coming Soon*: Instructions for creating standalone executables for Windows, macOS, and Linux.

## License

[License information to be added]

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing issues for solutions
- Review the developer documentation above

---

*Viseeonyx - Create beautiful collages with ease*