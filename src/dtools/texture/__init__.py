from .tex_details import TextureDetails
from .hex import HoneycombTexture, add_hex_texture_to_faces
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workplane import Workplane


def add_texture(
    workplane: "Workplane", details: TextureDetails, show_progress: bool = False
) -> "Workplane":
    if isinstance(details, HoneycombTexture):
        return add_hex_texture_to_faces(workplane, details, show_progress)
    else:
        raise ValueError(f"Invalid texture type: {type(details)}")


__all__ = ["TextureDetails", "HoneycombTexture", "add_hex_texture_to_faces"]
