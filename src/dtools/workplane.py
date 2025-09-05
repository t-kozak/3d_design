import enum
import logging
import math
from pathlib import Path
import random
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    Self,
    TYPE_CHECKING,
    Union,
    cast,
    override,
)

import cadquery as cq

from . import teardrop
from . import heatserts
from . import m_screw
from . import parabolic

_log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from .texture import TextureDetails


class Workplane(cq.Workplane):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_clean = True

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

    @override
    def cut(
        self,
        toCut: Union["cq.Workplane", cq.Solid, cq.Compound],
        clean: bool = True,
        tol: Optional[float] = None,
    ) -> Self:
        self.__merge_allow_clean(toCut)
        clean = clean and self.allow_clean
        _log.debug(f"cutting. clean? {clean}")
        return cast(Self, super().cut(toCut, clean, tol))

    def intersect(
        self,
        toIntersect: Union["cq.Workplane", cq.Solid, cq.Compound],
        clean: bool = True,
        tol: Optional[float] = None,
    ) -> Self:
        self.__merge_allow_clean(toIntersect)
        clean = clean and self.allow_clean
        return super().intersect(toIntersect, clean, tol)

    def union(
        self,
        toUnion: Optional[Union["cq.Workplane", cq.Solid, cq.Compound]] = None,
        clean: bool = True,
        glue: bool = False,
        tol: Optional[float] = None,
    ) -> Self:
        self.__merge_allow_clean(toUnion)
        clean = clean and self.allow_clean
        return super().union(toUnion, clean, glue, tol)

    def __merge_allow_clean(self, other) -> None:
        if not isinstance(other, Workplane):
            return
        _log.debug(
            f"merging allow clean. self.allow_clean: {self.allow_clean}, other.allow_clean: {other.allow_clean}"
        )
        self.allow_clean &= other.allow_clean
        self.allow_clean = False
        _log.debug(f"merged allow clean. self.allow_clean: {self.allow_clean}")

    def export(
        self,
        fname: str | Path,
        tolerance: float = 0.1,
        angularTolerance: float = 0.1,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Self:
        if isinstance(fname, Path):
            fname = str(fname)
        return super().export(fname, tolerance, angularTolerance, opt)
