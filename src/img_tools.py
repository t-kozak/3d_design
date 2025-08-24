from pathlib import Path
import numpy as np
from PIL import Image
import cadquery as cq
from tqdm import tqdm


def create_base_tiles(
    pixel_values: np.ndarray,
    width: float,
    height: float,
    min_depth: float,
    max_depth: float,
    invert: bool = False,
) -> list[cq.Workplane]:
    """
    Create base rectangular tiles for each pixel without unioning.

    Args:
        pixel_values: 2D numpy array of luminance levels
        width: Total width in millimeters
        height: Total height in millimeters
        min_depth: Minimum depth in millimeters
        max_depth: Maximum depth in millimeters
        invert: If True, darkest pixels become highest (inverted height mapping)

    Returns:
        List of CadQuery Workplane objects (one per pixel)
    """
    rows, cols = pixel_values.shape

    # Calculate pixel dimensions
    pixel_width = width / cols
    pixel_height = height / rows

    # Calculate depth scaling factor
    max_luminance = np.max(pixel_values)
    if max_luminance > 0:
        depth_per_luminance = (max_depth - min_depth) / max_luminance
    else:
        depth_per_luminance = 0

    tiles = []

    # Create progress bar
    total_pixels = rows * cols
    pbar = tqdm(total=total_pixels, desc="Creating base tiles", unit="pixel")

    for i in range(rows):
        for j in range(cols):
            # Get luminance level and calculate depth
            luminance_level = pixel_values[i, j]

            # Apply inversion if requested
            if invert:
                # Invert: darkest pixels (0) become highest, brightest become lowest
                inverted_level = max_luminance - luminance_level
                depth = min_depth + (inverted_level * depth_per_luminance)
            else:
                # Normal: brightest pixels become highest
                depth = min_depth + (luminance_level * depth_per_luminance)

            # Calculate position (centered around origin)
            x_pos = (j - cols / 2 + 0.5) * pixel_width
            y_pos = (height / 2 - i - 0.5) * pixel_height

            # Create tile
            tile = (
                cq.Workplane("XY")
                .box(pixel_width, pixel_height, depth)
                .translate((x_pos, y_pos, depth / 2))
            )

            tiles.append(tile)
            pbar.update(1)

    pbar.close()
    return tiles


def merge_adjacent_same_height_tiles(
    tiles: list[cq.Workplane],
    pixel_values: np.ndarray,
    width: float,
    height: float,
    tolerance: float = 0.01,
) -> list[cq.Workplane]:
    """
    Merge adjacent tiles with the same height to reduce union operations.

    Args:
        tiles: List of base tiles
        pixel_values: 2D numpy array of luminance levels
        width: Total width in millimeters
        height: Total height in millimeters
        tolerance: Height difference tolerance for merging (mm)

    Returns:
        List of merged tile groups
    """
    rows, cols = pixel_values.shape
    pixel_width = width / cols
    pixel_height = height / rows

    # Group tiles by height (with tolerance)
    height_groups = {}

    for i, tile in enumerate(tiles):
        row = i // cols
        col = i % cols
        height_val = pixel_values[row, col]

        # Find or create height group
        group_key = None
        for existing_height in height_groups.keys():
            if abs(existing_height - height_val) <= tolerance:
                group_key = existing_height
                break

        if group_key is None:
            group_key = height_val
            height_groups[group_key] = []

        height_groups[group_key].append((tile, row, col))

        # Merge adjacent tiles within each height group
    merged_groups = []

    # Calculate total work for progress bar
    total_height_groups = len(height_groups)
    pbar = tqdm(
        total=total_height_groups, desc="Processing height groups", unit="group"
    )

    for height_val, tile_list in height_groups.items():
        if len(tile_list) == 1:
            # Single tile, no merging needed
            merged_groups.append(tile_list[0][0])
            pbar.update(1)
            continue

        # Group tiles by adjacency
        adjacency_groups = []
        processed = set()

        for tile, row, col in tile_list:
            if (row, col) in processed:
                continue

            # Start new adjacency group
            current_group = [(tile, row, col)]
            processed.add((row, col))

            # Find all adjacent tiles recursively
            to_check = [(row, col)]
            while to_check:
                r, c = to_check.pop(0)

                # Check 4-connectivity (up, down, left, right)
                neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                for nr, nc in neighbors:
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in processed
                        and abs(pixel_values[nr, nc] - height_val) <= tolerance
                    ):

                        # Find the tile for this neighbor
                        neighbor_tile = None
                        for t, tr, tc in tile_list:
                            if tr == nr and tc == nc:
                                neighbor_tile = t
                                break

                        if neighbor_tile:
                            current_group.append((neighbor_tile, nr, nc))
                            processed.add((nr, nc))
                            to_check.append((nr, nc))

            # Merge tiles in this adjacency group
            if len(current_group) == 1:
                merged_groups.append(current_group[0][0])
            else:
                # Union all tiles in the group
                merged_tile = current_group[0][0]
                for t, _, _ in current_group[1:]:
                    merged_tile = merged_tile.union(t)
                merged_groups.append(merged_tile)

        pbar.update(1)

    pbar.close()

    print(f"Merged {len(tiles)} tiles into {len(merged_groups)} groups")
    return merged_groups


def fillet_tiles(
    tiles: list[cq.Workplane], fillet_radius: float = 0.2
) -> list[cq.Workplane]:
    """
    Apply fillets to all tiles for easier 3D printing.

    Args:
        tiles: List of tiles to fillet
        fillet_radius: Radius of the fillet in millimeters

    Returns:
        List of filleted tiles
    """
    filleted_tiles = []

    pbar = tqdm(total=len(tiles), desc="Applying fillets", unit="tile")

    for tile in tiles:
        try:
            # Apply fillet to edges perpendicular to Z axis
            filleted_tile = tile.faces("|Z").edges().fillet(fillet_radius)
            filleted_tiles.append(filleted_tile)
        except Exception as e:
            print(f"Warning: Could not fillet tile: {e}")
            filleted_tiles.append(tile)

        pbar.update(1)

    pbar.close()
    return filleted_tiles


def union_tiles_hierarchical(tiles: list, batch_size: int = 10) -> cq.Workplane:
    """
    Union tiles using a hierarchical tree approach for better performance.

    Args:
        tiles: List of CadQuery Workplane objects to union
        batch_size: Number of tiles to union in each batch

    Returns:
        Single CadQuery Workplane object representing the union of all tiles
    """
    if len(tiles) == 0:
        return cq.Workplane("XY")
    if len(tiles) == 1:
        return tiles[0]

    current_tiles = tiles.copy()

    while len(current_tiles) > 1:
        new_tiles = []
        num_batches = (len(current_tiles) + batch_size - 1) // batch_size

        # Progress update for large models
        if len(current_tiles) > 1:
            print(f"  Merging {len(current_tiles)} tiles into {num_batches} batches...")

        # Process tiles in batches with progress bar
        with tqdm(
            total=num_batches,
            desc=f"  Level {len(current_tiles)}→{num_batches}",
            unit="batch",
        ) as pbar:
            for i in range(0, len(current_tiles), batch_size):
                batch = current_tiles[i : i + batch_size]

                if len(batch) == 1:
                    # Single tile, no union needed
                    new_tiles.append(batch[0])
                else:
                    # Union the batch
                    batch_result = batch[0]
                    for tile in batch[1:]:
                        batch_result = batch_result.union(tile)
                    new_tiles.append(batch_result)

                pbar.update(1)

        # Replace current tiles with the new merged tiles
        current_tiles = new_tiles

    return current_tiles[0]


def image_to_grayscale(
    img_path: Path, grey_depth: int = 16, cols: int = 128, rows: int = 128
) -> np.ndarray:
    """
    Convert an image to grayscale and quantize it to specified resolution.

    Args:
        img_path: Path to the input image
        grey_depth: Number of gray levels (e.g., 8 for 256 levels, 4 for 16 levels)
        cols: Number of columns in output
        rows: Number of rows in output

    Returns:
        2D numpy array of pixel values representing the quantized grayscale image
    """
    # Open the image
    with Image.open(img_path) as img:
        # Convert to grayscale
        gray_img = img.convert("L")

        # Convert to numpy array for manipulation
        img_array = np.array(gray_img)

        # Quantize to specified gray depth - use actual image dynamic range
        # Find the actual min/max values in the image
        img_min = np.min(img_array)
        img_max = np.max(img_array)
        img_range = img_max - img_min

        num_levels = grey_depth
        step_size = img_range / (num_levels - 1) if num_levels > 1 else img_range

        # Create discrete levels spanning the actual image range
        levels = img_min + np.arange(num_levels) * step_size
        levels = np.round(levels).astype(int)

        # Ensure the last level is exactly the max value for full white
        levels[-1] = img_max

        # Quantize each pixel to nearest discrete level
        quantized_array = np.zeros_like(img_array, dtype=int)
        level_indices = np.zeros_like(
            img_array, dtype=int
        )  # Store level indices (0 to grey_depth-1)

        for i, level in enumerate(levels):
            if i == 0:
                # First level: everything below the first threshold
                threshold = img_min + step_size / 2
                mask = img_array < threshold
            elif i == num_levels - 1:
                # Last level: everything above the previous threshold
                threshold = img_min + (i * step_size - step_size / 2)
                mask = img_array >= threshold
            else:
                # Middle levels: between thresholds
                lower_threshold = img_min + (i * step_size - step_size / 2)
                upper_threshold = img_min + (i * step_size + step_size / 2)
                mask = (img_array >= lower_threshold) & (img_array < upper_threshold)

            quantized_array[mask] = level
            level_indices[mask] = (
                i  # Store the level index (0, 1, 2, ..., grey_depth-1)
            )

        # Save intermediate grayscale image (after quantization, full resolution)
        output_dir = img_path.parent
        input_name = img_path.stem
        gray_output_path = output_dir / f"{input_name}_greyscale.png"

        # Convert quantized array back to PIL Image for saving
        gray_output_img = Image.fromarray(quantized_array.astype(np.uint8))
        gray_output_img.save(gray_output_path)

        # Downscale to target resolution
        resized_img = gray_output_img.resize((cols, rows), Image.Resampling.LANCZOS)
        final_array = np.array(resized_img)

        # Save final quantized image (downscaled)
        final_output_path = output_dir / f"{input_name}_final.png"
        final_img = Image.fromarray(final_array.astype(np.uint8))
        final_img.save(final_output_path)

        # Downscale the level indices to target resolution
        # We need to map the brightness values back to level indices
        final_level_indices = np.zeros((rows, cols), dtype=int)
        for i in range(rows):
            for j in range(cols):
                brightness = final_array[i, j]
                # Find which level this brightness corresponds to
                level_idx = np.argmin(np.abs(levels - brightness))
                final_level_indices[i, j] = level_idx

        # Return level indices (0 to grey_depth-1)
        return final_level_indices


def img_2_3d(
    pixel_values: np.ndarray,
    width: float = 100.0,
    height: float = 100.0,
    min_depth: float = 0.2,
    max_depth: float = 5.0,
    fillet_radius: float = 0.2,
    invert: bool = False,
) -> cq.Workplane:
    """
    Convert a 2D pixel array into a 3D printed mosaic using CadQuery.

    Args:
        pixel_values: 2D numpy array where each value represents a luminance level (0 to max_level)
        width: Total width of the mosaic in millimeters
        height: Total height of the mosaic in millimeters
        min_depth: Minimum depth (height) for pixels with zero luminance in millimeters
        max_depth: Maximum depth (height) for pixels with maximum luminance in millimeters
        fillet_radius: Radius of the fillet for easier 3D printing
        invert: If True, darkest pixels become highest (inverted height mapping)

    Returns:
        CadQuery Workplane object representing the 3D mosaic
    """
    print("Stage: Creating base tiles...")
    base_tiles = create_base_tiles(
        pixel_values, width, height, min_depth, max_depth, invert
    )

    # print("Stage 2: Merging adjacent same-height tiles...")
    # merged_tiles = merge_adjacent_same_height_tiles(
    #     base_tiles, pixel_values, width, height
    # )

    # print("Stage 3: Applying fillets...")
    # filleted_tiles = fillet_tiles(merged_tiles, fillet_radius)

    print("Stage: Final unioning...")
    result = union_tiles_hierarchical(base_tiles, batch_size=10)

    return result


if __name__ == "__main__":
    # Test the image processing
    pixel_array = image_to_grayscale(Path("airpods.jpg"), cols=128, rows=128)

    # Create 3D mosaic
    mosaic = img_2_3d(
        pixel_array,
        width=90.0,
        height=90.0,
        min_depth=1.0,
        max_depth=8.0,
        invert=False,
    )

    # Export to STL
    cq.exporters.export(mosaic, "airpods.stl")
