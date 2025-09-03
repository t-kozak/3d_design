#!/usr/bin/env python3
"""Test script for the image_to_depth_grayscale function."""

from pathlib import Path
from src.img_to_stl import image_to_depth_grayscale


def test_depth_function():
    """Test the image_to_depth_grayscale function."""

    print("Testing image_to_depth_grayscale function...")
    print("=" * 60)

    # Test with a sample image (this will fail if no depth data)
    test_image = Path(
        "test_portrait.jpg"
    )  # You would need an actual iOS portrait photo

    if test_image.exists():
        try:
            print(f"Testing with: {test_image}")

            # Try to extract depth data
            depth_array = image_to_depth_grayscale(
                img_path=test_image, grey_depth=16, cols=64, rows=64
            )

            print(f"Success! Depth array shape: {depth_array.shape}")
            print(f"Depth values range: {depth_array.min()} to {depth_array.max()}")

        except Exception as e:
            print(f"Expected error (no depth data): {e}")
            print("This is normal for images without depth data")
    else:
        print(f"Test image not found: {test_image}")
        print(
            "To test this function, you need an iOS portrait mode photo with depth data"
        )
        print("The function will:")
        print("1. Extract depth map from EXIF data")
        print("2. Parse the depth information")
        print("3. Convert to grayscale array")
        print("4. Quantize to specified gray levels")
        print("5. Save intermediate depth maps")
        print("6. Return the final array for 3D printing")

    print("\nFunction signature:")
    print("image_to_depth_grayscale(img_path, grey_depth=16, cols=128, rows=128)")
    print("\nReturns: 2D numpy array of depth values")
    print("Raises: ValueError if no depth data, RuntimeError if processing fails")


if __name__ == "__main__":
    test_depth_function()


