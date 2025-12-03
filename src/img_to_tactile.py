#!/usr/bin/env python3
"""
Image to Tactile Mesh Converter
Takes an image and converts it to a 3D mesh using depth estimation for tactile exploration.

Usage:
    python image_to_tactile_mesh.py input_image.jpg --output output.stl
"""

import argparse

import numpy as np
import torch
import trimesh
from PIL import Image
from transformers import pipeline


def load_depth_model(model_size="base"):
    """
    Load the Depth Anything V2 model.

    Args:
        model_size: 'small', 'base', or 'large'

    Returns:
        Depth estimation pipeline
    """
    model_names = {
        "small": "depth-anything/Depth-Anything-V2-Small-hf",
        "base": "depth-anything/Depth-Anything-V2-Base-hf",
        "large": "depth-anything/Depth-Anything-V2-Large-hf",
    }

    model_name = model_names.get(model_size, model_names["base"])

    # Use Metal (MPS) on macOS if available, otherwise fall back to CPU
    if torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"Loading {model_name} on {device}...")
    pipe = pipeline(task="depth-estimation", model=model_name, device=device)

    return pipe


def estimate_depth(pipe, image_path, target_width=None):
    """
    Estimate depth from an image.

    Args:
        pipe: Depth estimation pipeline
        image_path: Path to input image
        target_width: Optional width to resize image (maintains aspect ratio)

    Returns:
        Normalized depth map as numpy array
    """
    print(f"Loading image: {image_path}")
    image = Image.open(image_path).convert("RGB")

    # Optionally resize for faster processing
    if target_width and image.width > target_width:
        aspect_ratio = image.height / image.width
        target_height = int(target_width * aspect_ratio)
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        print(f"Resized to: {target_width}x{target_height}")

    print("Estimating depth...")
    result = pipe(image)

    # Get the depth tensor and convert to numpy
    depth = result["predicted_depth"].cpu().numpy()

    # Normalize to 0-1 range (closer objects = higher values)
    depth_normalized = (depth - depth.min()) / (depth.max() - depth.min())

    return depth_normalized, image.size


def create_mesh_from_depth(
    depth_map,
    width,
    height,
    base_thickness=2.0,
    max_relief_height=10.0,
    physical_width=100.0,
    smooth=False,
):
    """
    Create a 3D mesh from a depth map.

    Args:
        depth_map: 2D numpy array with normalized depth values (0-1)
        width: Width of the depth map in pixels
        height: Height of the depth map in pixels
        base_thickness: Thickness of the base plate in mm
        max_relief_height: Maximum height of the relief in mm
        physical_width: Physical width of the final model in mm
        smooth: Whether to apply smoothing to the mesh

    Returns:
        trimesh.Trimesh object
    """
    print("Creating mesh...")

    # Calculate physical dimensions maintaining aspect ratio
    aspect_ratio = height / width
    physical_height = physical_width * aspect_ratio

    # Flip depth map vertically to correct mirror reflection
    depth_map = np.flipud(depth_map)

    # Create coordinate grids
    rows, cols = depth_map.shape

    # Downsample if resolution is too high (for manageable file size)
    max_resolution = 750
    if rows > max_resolution or cols > max_resolution:
        scale_factor = max_resolution / max(rows, cols)
        new_rows = int(rows * scale_factor)
        new_cols = int(cols * scale_factor)
        depth_map = np.array(
            Image.fromarray(depth_map).resize(
                (new_cols, new_rows), Image.Resampling.LANCZOS
            )
        )
        rows, cols = depth_map.shape
        print(f"Downsampled mesh resolution to: {cols}x{rows}")

    # Create mesh grid
    x = np.linspace(0, physical_width, cols)
    y = np.linspace(0, physical_height, rows)
    X, Y = np.meshgrid(x, y)

    # Z values: base + relief height based on depth
    Z = base_thickness + (depth_map * max_relief_height)

    # Create vertices for top surface
    vertices_top = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

    # Create vertices for bottom surface (flat base)
    Z_bottom = np.zeros_like(Z)
    vertices_bottom = np.stack([X.ravel(), Y.ravel(), Z_bottom.ravel()], axis=1)

    # Combine all vertices
    vertices = np.vstack([vertices_top, vertices_bottom])

    # Create faces for top surface
    faces_top = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Top-left triangle
            v1 = i * cols + j
            v2 = i * cols + (j + 1)
            v3 = (i + 1) * cols + j
            faces_top.append([v1, v2, v3])

            # Bottom-right triangle
            v1 = i * cols + (j + 1)
            v2 = (i + 1) * cols + (j + 1)
            v3 = (i + 1) * cols + j
            faces_top.append([v1, v2, v3])

    # Create faces for bottom surface (reversed winding)
    offset = len(vertices_top)
    faces_bottom = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            v1 = offset + i * cols + j
            v2 = offset + (i + 1) * cols + j
            v3 = offset + i * cols + (j + 1)
            faces_bottom.append([v1, v2, v3])

            v1 = offset + i * cols + (j + 1)
            v2 = offset + (i + 1) * cols + j
            v3 = offset + (i + 1) * cols + (j + 1)
            faces_bottom.append([v1, v2, v3])

    # Create side faces
    faces_sides = []

    # Left edge
    for i in range(rows - 1):
        v1 = i * cols
        v2 = (i + 1) * cols
        v3 = offset + i * cols
        faces_sides.append([v1, v2, v3])

        v1 = (i + 1) * cols
        v2 = offset + (i + 1) * cols
        v3 = offset + i * cols
        faces_sides.append([v1, v2, v3])

    # Right edge
    for i in range(rows - 1):
        v1 = i * cols + (cols - 1)
        v2 = offset + i * cols + (cols - 1)
        v3 = (i + 1) * cols + (cols - 1)
        faces_sides.append([v1, v2, v3])

        v1 = (i + 1) * cols + (cols - 1)
        v2 = offset + i * cols + (cols - 1)
        v3 = offset + (i + 1) * cols + (cols - 1)
        faces_sides.append([v1, v2, v3])

    # Top edge
    for j in range(cols - 1):
        v1 = j
        v2 = offset + j
        v3 = j + 1
        faces_sides.append([v1, v2, v3])

        v1 = j + 1
        v2 = offset + j
        v3 = offset + j + 1
        faces_sides.append([v1, v2, v3])

    # Bottom edge
    for j in range(cols - 1):
        v1 = (rows - 1) * cols + j
        v2 = (rows - 1) * cols + j + 1
        v3 = offset + (rows - 1) * cols + j
        faces_sides.append([v1, v2, v3])

        v1 = (rows - 1) * cols + j + 1
        v2 = offset + (rows - 1) * cols + j + 1
        v3 = offset + (rows - 1) * cols + j
        faces_sides.append([v1, v2, v3])

    # Combine all faces
    faces = np.vstack([faces_top, faces_bottom, faces_sides])

    # Create mesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    # Fix normals and remove degenerate faces
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.fix_normals()

    if smooth:
        print("Applying surface smoothing...")
        trimesh.smoothing.filter_laplacian(mesh, iterations=3)

    # Ensure mesh is watertight
    if not mesh.is_watertight:
        print("Warning: Mesh is not watertight. Attempting to fix...")
        mesh.fill_holes()

    print(f"Mesh created: {len(vertices)} vertices, {len(faces)} faces")
    print(
        f"Physical dimensions: {physical_width:.1f}mm x {physical_height:.1f}mm x {base_thickness + max_relief_height:.1f}mm"
    )
    print(f"Mesh is watertight: {mesh.is_watertight}")

    return mesh


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image to a tactile 3D mesh using depth estimation"
    )
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument(
        "--output", "-o", default="output.stl", help="Output file path (.stl or .obj)"
    )
    parser.add_argument(
        "--model-size",
        choices=["small", "base", "large"],
        default="base",
        help="Model size (small=fastest, large=most accurate)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Target width in pixels for processing (for speed)",
    )
    parser.add_argument(
        "--physical-width",
        type=float,
        default=100.0,
        help="Physical width of the model in mm",
    )
    parser.add_argument(
        "--base-thickness", type=float, default=2.0, help="Base thickness in mm"
    )
    parser.add_argument(
        "--max-height", type=float, default=10.0, help="Maximum relief height in mm"
    )
    parser.add_argument(
        "--smooth", action="store_true", help="Apply surface smoothing"
    )
    parser.add_argument(
        "--save-depth-map", action="store_true", help="Save the depth map as an image"
    )

    args = parser.parse_args()

    # Load model
    pipe = load_depth_model(args.model_size)

    # Estimate depth
    depth_map, (width, height) = estimate_depth(pipe, args.input_image, args.width)

    # Optionally save depth map
    if args.save_depth_map:
        depth_image = Image.fromarray((depth_map * 255).astype(np.uint8))
        depth_output = args.output.rsplit(".", 1)[0] + "_depth.png"
        depth_image.save(depth_output)
        print(f"Depth map saved to: {depth_output}")

    # Create mesh
    mesh = create_mesh_from_depth(
        depth_map,
        width,
        height,
        base_thickness=args.base_thickness,
        max_relief_height=args.max_height,
        physical_width=args.physical_width,
        smooth=args.smooth,
    )

    # Export mesh
    print(f"Exporting to: {args.output}")
    mesh.export(args.output)

    print("Done!")


if __name__ == "__main__":
    main()
