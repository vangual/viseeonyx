# src/arrangement.py

def arrange_no_resize(image_objects, canvas_size):
    """
    Arrange all image objects in a simple flow layout (left to right, top to bottom),
    without resizing them.
    """
    if not image_objects:
        return
    x_margin = 10
    y_margin = 10
    spacing = 10

    current_x = x_margin
    current_y = y_margin
    max_height_in_row = 0

    canvas_w, canvas_h = canvas_size

    for obj in image_objects:
        w = obj.width
        h = obj.height

        if current_x + w > canvas_w - x_margin:
            # move to next row
            current_x = x_margin
            current_y += max_height_in_row + spacing
            max_height_in_row = 0

        obj.x = current_x
        obj.y = current_y
        current_x += w + spacing
        if h > max_height_in_row:
            max_height_in_row = h


def arrange_with_resize(image_objects, canvas_size):
    """
    Arrange and resize objects so that they fit in a simple grid, keeping aspect ratios.
    """
    if not image_objects:
        return
    canvas_w, canvas_h = canvas_size
    # We'll do a naive approach: compute a grid NxN that can hold all objects
    import math
    count = len(image_objects)
    grid_cols = int(math.ceil(math.sqrt(count)))
    grid_rows = int(math.ceil(count / grid_cols))

    cell_w = canvas_w // grid_cols
    cell_h = canvas_h // grid_rows

    for idx, obj in enumerate(image_objects):
        row = idx // grid_cols
        col = idx % grid_cols

        # We want to fit the object's aspect ratio into cell_w x cell_h
        # We'll guess the best width/height
        obj.load_image()
        aspect = obj._aspect_ratio if obj._aspect_ratio else 1.0
        # Fit by width first
        new_w = cell_w
        new_h = int(new_w / aspect)
        if new_h > cell_h:
            # Fit by height instead
            new_h = cell_h
            new_w = int(new_h * aspect)

        obj.width = new_w
        obj.height = new_h
        obj.zoom_factor = 1.0  # reset zoom, or adjust if you want

        x = col * cell_w + (cell_w - new_w) // 2
        y = row * cell_h + (cell_h - new_h) // 2
        obj.x = x
        obj.y = y
        obj.viewport_offset = (0, 0)  # reset
