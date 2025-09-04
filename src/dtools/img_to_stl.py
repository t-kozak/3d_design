from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm
from stl import mesh


def grayscale_to_stl(
    pixel_values: np.ndarray,
    width: float,
    height: float,
    depth_min: float,
    depth_max: float,
    output_path: Path | None = None,
) -> mesh.Mesh:
    """
    Convert a grayscale numpy array to a 3D STL mesh.

    Args:
        pixel_values: 2D numpy array with luminance values (0 to max_value)
        width: Total width in millimeters
        height: Total height in millimeters
        depth_min: Minimum depth in millimeters
        depth_max: Maximum depth in millimeters
        output_path: Optional path to save the STL file

    Returns:
        STL mesh object
    """
    rows, cols = pixel_values.shape

    # Calculate pixel dimensions
    pixel_width = width / cols
    pixel_height = height / rows

    # Calculate depth scaling factor
    max_value = np.max(pixel_values)
    if max_value == 0:
        max_value = 1  # Avoid division by zero

    # Create vertices for top and bottom faces
    vertices = []
    faces = []

    # Generate vertices for each pixel
    for i in range(rows):
        for j in range(cols):
            # Calculate x, y positions
            x = j * pixel_width
            y = i * pixel_height

            # Calculate z depth based on pixel value
            pixel_value = pixel_values[i, j]
            z_top = depth_min + ((depth_max - depth_min) * pixel_value / max_value)
            z_bottom = 0.0

            # Add top vertex
            vertices.append([x, y, z_top])
            # Add bottom vertex
            vertices.append([x, y, z_bottom])

    # Convert to numpy array
    vertices = np.array(vertices)

    # Generate faces
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Calculate vertex indices for current pixel
            # Each pixel has 2 vertices (top and bottom)
            current_top = (i * cols + j) * 2
            current_bottom = current_top + 1
            right_top = (i * cols + (j + 1)) * 2
            right_bottom = right_top + 1
            below_top = ((i + 1) * cols + j) * 2
            below_bottom = below_top + 1
            below_right_top = ((i + 1) * cols + (j + 1)) * 2
            below_right_bottom = below_right_top + 1

            # Top face (2 triangles)
            # Triangle 1: current_top, right_top, below_top
            faces.append([current_top, right_top, below_top])
            # Triangle 2: right_top, below_right_top, below_top
            faces.append([right_top, below_right_top, below_top])

            # Bottom face (2 triangles)
            # Triangle 1: current_bottom, below_bottom, right_bottom
            faces.append([current_bottom, below_bottom, right_bottom])
            # Triangle 2: right_bottom, below_bottom, below_right_bottom
            faces.append([right_bottom, below_bottom, below_right_bottom])

            # Side faces (4 triangles connecting top to bottom)
            # Front face (current pixel)
            faces.append([current_top, below_top, current_bottom])
            faces.append([below_top, below_bottom, current_bottom])

            # Right face (right pixel)
            faces.append([right_top, right_bottom, below_right_top])
            faces.append([below_right_top, right_bottom, below_right_bottom])

            # Back face (below pixel)
            faces.append([below_top, below_right_top, below_bottom])
            faces.append([below_right_top, below_right_bottom, below_bottom])

            # Left face (current pixel)
            faces.append([current_top, current_bottom, right_top])
            faces.append([right_top, current_bottom, right_bottom])

    # Convert faces to numpy array
    faces = np.array(faces)

    # Create the mesh

    stl_mesh: mesh.Mesh = mesh.Mesh(  # type:ignore
        np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype)
    )  # type:ignore

    # Set vertices and faces
    for i, face in enumerate(faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = vertices[face[j]]

    # Save to file if output path is provided
    if output_path:
        stl_mesh.save(str(output_path))
        print(f"STL file saved to: {output_path}")

    return stl_mesh


def invert_luminance(pixel_values: np.ndarray) -> np.ndarray:
    """
    Invert the luminance values in a 2D numpy array.

    This function flips the luminance values so that:
    - Dark pixels (low values) become bright (high values)
    - Bright pixels (high values) become dark (low values)

    Args:
        pixel_values: 2D numpy array with luminance values

    Returns:
        2D numpy array with inverted luminance values

    Example:
        If input has values [0, 50, 100, 255],
        output will be [255, 205, 155, 0]
    """
    if pixel_values.size == 0:
        return pixel_values

    # Get the maximum value in the array
    max_value = np.max(pixel_values)

    # Invert: new_value = max_value - original_value
    inverted_array = max_value - pixel_values

    return inverted_array


def image_to_grayscale(
    img_path: Path, grey_depth: int = 16, cols: int = 128, rows: int = 128
) -> np.ndarray:
    """
    Convert an image to grayscale and quantize it to specified resolution.

    Args:
        img_path: Path to the input image
        grey_depth: Number of gray levels with discrete amount of luminance levels
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


def img_to_stl(
    img_path: Path,
    output_path: Path,
    rows: int = 128,
    cols: int = 128,
    width: float = 100.0,
    height: float = 100.0,
    depth_min: float = 1.0,
    depth_max: float = 5.0,
    grey_depth: int = 16,
) -> mesh.Mesh:
    """
    Convert an image directly to a 3D STL mosaic in one function call.

    This function combines image_to_grayscale and grayscale_to_stl into a single
    convenient interface for converting images to 3D printable STL files.

    Args:
        img_path: Path to the input image file
        output_path: Path where the STL file will be saved
        rows: Number of rows in the output (default: 128)
        cols: Number of columns in the output (default: 128)
        width: Total width of the mosaic in millimeters (default: 100.0)
        height: Total height of the mosaic in millimeters (default: 100.0)
        depth_min: Minimum depth in millimeters (default: 1.0)
        depth_max: Maximum depth in millimeters (default: 5.0)
        grey_depth: Number of gray levels for quantization (default: 16)

    Returns:
        STL mesh object

    Raises:
        FileNotFoundError: If the input image doesn't exist
        ValueError: If any of the dimension parameters are invalid
    """
    # Validate input parameters
    if not img_path.exists():
        raise FileNotFoundError(f"Input image not found: {img_path}")

    if rows <= 0 or cols <= 0:
        raise ValueError("Rows and columns must be positive integers")

    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive numbers")

    if depth_min < 0 or depth_max <= depth_min:
        raise ValueError("depth_min must be >= 0 and depth_max must be > depth_min")

    if grey_depth < 2:
        raise ValueError("grey_depth must be at least 2")

    print(f"Converting image to 3D STL mosaic...")
    print(f"Input: {img_path}")
    print(f"Output: {output_path}")
    print(f"Resolution: {cols}x{rows} pixels")
    print(f"Dimensions: {width}x{height} mm")
    print(f"Depth range: {depth_min}-{depth_max} mm")
    print(f"Gray levels: {grey_depth}")

    # Step 1: Convert image to grayscale array
    print("\nStep 1: Converting image to grayscale...")
    grayscale_array = image_to_grayscale(
        img_path=img_path, grey_depth=grey_depth, cols=cols, rows=rows
    )

    print(f"Grayscale conversion complete. Array shape: {grayscale_array.shape}")
    print(f"Value range: {grayscale_array.min()} to {grayscale_array.max()}")

    # Step 2: Convert grayscale array to STL
    print("\nStep 2: Generating 3D STL mesh...")
    stl_mesh = grayscale_to_stl(
        pixel_values=grayscale_array,
        width=width,
        height=height,
        depth_min=depth_min,
        depth_max=depth_max,
        output_path=output_path,
    )

    print(f"\nConversion complete!")
    print(f"STL file saved to: {output_path}")
    print(f"Mesh contains {len(stl_mesh.vectors)} triangles")

    return stl_mesh


if __name__ == "__main__":
    imgs = ["dad", "clam", "mountain", "airpods"]

    for img in imgs:
        input_img = Path(f"images/{img}.jpg")
        if input_img.exists():
            print(f"\n{'='*60}")
            print(f"Processing: {img}")
            print(f"{'='*60}")

            # Process normal version
            output_stl = Path(f"{img}.stl")
            try:
                img_to_stl(input_img, output_stl)
            except Exception as e:
                print(f"Error processing normal version: {e}")

            # Process inverted version
            output_stl_inverted = Path(f"{img}_inverted.stl")
            try:
                # First convert to grayscale
                grayscale_array = image_to_grayscale(input_img, cols=128, rows=128)

                # Invert the luminance
                inverted_array = invert_luminance(grayscale_array)

                # Convert inverted array to STL
                stl_mesh = grayscale_to_stl(
                    pixel_values=inverted_array,
                    width=100.0,
                    height=100.0,
                    depth_min=1.0,
                    depth_max=8.0,
                    output_path=output_stl_inverted,
                )

                print(f"Inverted version saved to: {output_stl_inverted}")
                print(f"Inverted mesh has {len(stl_mesh.vectors)} triangles")

            except Exception as e:
                print(f"Error processing inverted version: {e}")
        else:
            print(f"Image not found: {input_img}")
