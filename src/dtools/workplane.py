import enum
import math
import random
from typing import Literal, Self, cast, TYPE_CHECKING

import cadquery as cq


from . import teardrop
from . import heatserts
from . import m_screw
from . import parabolic

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
        self,
        screw: m_screw.MScrew,
        core_length: float,
        head_on_top: bool = True,
        head_height: float | None = None,
    ) -> Self:
        return cast(
            Self,
            m_screw.create_screw_hole(
                self, screw, core_length, head_on_top, head_height
            ),
        )

    def parabolic_channel(
        self,
        length=60.0,
        width=40.0,
        side_thickness=10.0,
        top_thickness=10.0,
    ) -> Self:
        return cast(
            Self,
            parabolic.parabolic_channel(
                self,
                length,
                width,
                side_thickness,
                top_thickness,
            ),
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

    def rotate_center(self, axis: Literal["X", "Y", "Z"], angle: float) -> Self:
        center = self.get_center()
        if axis == "X":
            start_vector = (center.x, center.y, center.z)
            end_vector = (center.x + 1, center.y, center.z)
        elif axis == "Y":
            start_vector = (center.x, center.y, center.z)
            end_vector = (center.x, center.y + 1, center.z)
        elif axis == "Z":
            start_vector = (center.x, center.y, center.z)
            end_vector = (center.x, center.y, center.z + 1)
        return self.rotate(start_vector, end_vector, angle)
