import enum
import math
import random
from typing import Literal, Self, cast, TYPE_CHECKING

import cadquery as cq


from . import teardrop
from . import heatserts
from . import m_screw

if TYPE_CHECKING:
    from .texture import TextureDetails


class Workplane(cq.Workplane):
    def teardrop(
        self, radius: float = 1, rotate: float = 0, clip: float | None = None
    ) -> Self:
        return cast(Self, teardrop.teardrop(self, radius, rotate, clip))

    def heatsert(
        self,
        size: m_screw.MScrew = m_screw.MScrew.M4,
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
            val = self.val()
            assert isinstance(val, cq.Vector)
            current_pos = val
            x += current_pos.x
            y += current_pos.y

        # Delegate to base class moveTo method
        return cast(Self, self.moveTo(x, y))

    def screw_core_hole(self, screw: m_screw.MScrew, depth: float) -> Self:
        return cast(Self, m_screw.create_screw_core_hole(self, screw, depth))

    def screw_hole(
        self, screw: m_screw.MScrew, body_depth: float, head_on_top: bool = True
    ) -> Self:
        return cast(
            Self, m_screw.create_screw_hole(self, screw, body_depth, head_on_top)
        )

    def get_center(self) -> cq.Vector:
        val = self.val()
        if isinstance(val, cq.Vector):
            return val
        elif isinstance(val, cq.Shape):
            return val.BoundingBox().center
        else:
            raise ValueError(f"Invalid type: {type(val)}")

    def get_bbox(self) -> cq.BoundBox:
        val = self.val()
        if isinstance(val, cq.Shape):
            return val.BoundingBox()
        else:
            raise ValueError(f"Invalid type: {type(val)}")
