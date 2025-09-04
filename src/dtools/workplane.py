import enum
import math
import random
from typing import Literal, Self, cast, TYPE_CHECKING

import cadquery as cq

from .m_screw import MScrew
from . import teardrop
from . import heatserts

if TYPE_CHECKING:
    from .texture import TextureDetails


class Workplane(cq.Workplane):
    def teardrop(
        self, radius: float = 1, rotate: float = 0, clip: float | None = None
    ) -> Self:
        return cast(Self, teardrop.teardrop(self, radius, rotate, clip))

    def heatsert(
        self,
        size: MScrew = MScrew.M4,
        depth: float | None = None,
    ) -> Self:
        return cast(Self, heatserts.heatsert(self, size, depth))

    def texture(self, details: "TextureDetails", show_progress: bool = False) -> Self:
        # Import here to avoid circular import
        from .texture import add_texture

        return cast(Self, add_texture(self, details, show_progress))

    def polar_move_to(self, phi: float, r: float, relative: bool = False) -> Self:
        # Convert polar coordinates to Cartesian
        x = r * math.cos(phi)
        y = r * math.sin(phi)

        if relative:
            # Get current position and add the calculated offset
            current_pos = self.plane.origin
            x += current_pos.x
            y += current_pos.y

        # Delegate to base class moveTo method
        return cast(Self, self.moveTo(x, y))

    def get_center(self) -> cq.Vector:
        val = self.val()
        if isinstance(val, cq.Vector):
            return val
        elif isinstance(val, cq.Shape):
            return val.BoundingBox().center
        else:
            raise ValueError(f"Invalid type: {type(val)}")
