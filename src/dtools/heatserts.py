import cadquery as cq
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .m_screw import MScrew


def heatsert(
    workplane: cq.Workplane,
    size: "MScrew | None" = None,
    depth: float | None = None,
    depth_clearance: float = 0.2,
    guide_hole_location: Literal["top", "bottom"] | None = None,
    guide_hole_depth: float = 0.5,
    guide_hole_clearance: float = 0.2,
):
    from .m_screw import MScrew

    size = size or MScrew.M4
    depth = size.heatsert_depth if depth is None else depth
    hole = workplane.circle(size.heatsert_diameter / 2).extrude(depth + depth_clearance)
    if guide_hole_location is not None:
        guide_hole = workplane.circle(
            size.heatsert_diameter / 2 + guide_hole_clearance
        ).extrude(guide_hole_depth)
        if guide_hole_location == "top":
            guide_hole = guide_hole.translate(
                (0, 0, depth + depth_clearance - guide_hole_depth)
            )
        hole += guide_hole

    return hole
