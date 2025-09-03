import cadquery as cq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .m_screw import MScrew


def heatsert(
    workplane: cq.Workplane,
    size: "MScrew | None" = None,
    depth: float | None = None,
):
    from .m_screw import MScrew

    size = size or MScrew.M4
    depth = size.heatsert_depth if depth is None else depth
    return workplane.circle(size.heatsert_diameter / 2).extrude(depth)
