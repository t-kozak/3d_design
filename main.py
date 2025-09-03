#!/usr/bin/env python3
"""
Main script to run the 3D design modules.
This script uses the proper package structure.

Run with: uv run python main.py
"""

if __name__ == "__main__":
    from src.dbox import ParametricDrawerBox
    from ocp_vscode import show

    # Create and display the drawer box
    dbox = ParametricDrawerBox(
        content_width=150.0,
        content_length=100.0,
        content_height=20.0,
    )
    show(dbox.create_assembly(), axes=True, axes0=True)
