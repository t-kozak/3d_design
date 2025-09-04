from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from ocp_vscode import show

from design_tools.workplane import Workplane

assert show is not None


@dataclass
class MeasuredDims:
    sheet_thickness: float = 0.3
    sheet_width: float = 170.0
    tap_pipe_diameter: float = 44.7
    tap_to_sink_edge_distance: float = 33.1
    tap_control_to_slab_dist = 40.5


md = MeasuredDims()


@dataclass
class Dims:
    base_length: float = 120.0
    base_width: float = 15.0
    tap_control_pipe_point = (
        md.tap_to_sink_edge_distance + (md.tap_pipe_diameter / 2),
        md.tap_control_to_slab_dist * 0.7,
    )

    base_max_height: float = 55.0
    base_min_height: float = 3.0

    groove_offset: float = 0.1
    groove_thickness: float = md.sheet_thickness * 2
    groove_width: float = 10.0
    leg_height = 2


d = Dims()


def make_leg():
    return Workplane("XY").sphere(d.leg_height)


def make_holder_triangle(left: bool) -> Workplane:
    main_body = (
        Workplane("YZ")
        .lineTo(d.base_length, 0)
        .lineTo(d.base_length, d.base_max_height)
        .close()
        .extrude(d.base_width)
        .edges("|X")
        .fillet(2)
    )

    main_body_big_hole = (
        Workplane("YZ")
        .moveTo(20, 5)
        .lineTo(d.base_length - 10, 5)
        .lineTo(d.base_length - 10, d.base_max_height - 10)
        .close()
        .extrude(d.base_width)
        .edges("|X")
        .fillet(1)
    )

    groove_profile = Workplane("XZ").rect(
        d.groove_width, d.groove_thickness, centered=False
    )
    groove_path = Workplane("YZ").lineTo(d.base_length, d.base_max_height)

    sheet_groove = groove_profile.sweep(groove_path).translate(
        (d.base_width - d.groove_width, 10, 2)
    )
    leg_lower_x = 3
    leg_upper_x = 11.5
    leg_lower_y = 25
    leg_upper_y = 100
    z_offset = 1  # -d.leg_height * 0.02
    legs = [
        make_leg().translate((leg_lower_x, leg_lower_y, z_offset)),
        make_leg().translate((leg_lower_x, leg_upper_y, z_offset)),
        make_leg().translate((leg_upper_x, leg_lower_y, z_offset)),
        make_leg().translate((leg_upper_x, leg_upper_y, z_offset)),
    ]

    hole_radius = 3
    hole_radius_height = 18
    support_hole = (
        Workplane("XY")
        .teardrop(hole_radius)
        .extrude(hole_radius_height)
        .rotate((0, 0, 0), (0, 0, 1), 270)
        .rotate((0, 0, 0), (1, 0, 0), 15)
        .translate(
            (
                d.base_width - hole_radius * 1.8,
                d.base_length * 0.96,
                d.base_max_height - hole_radius_height * 0.8,
            )
        )
    )

    edge_stopper = (
        Workplane("YZ")
        .rect(3, 7, centered=False)
        .extrude(d.base_width)
        .edges("|X and <Z")
        .fillet(1)
        .translate((0, 10, -5))
    )

    all = main_body - sheet_groove - main_body_big_hole - support_hole + edge_stopper
    for leg in legs:
        all += leg

    if not left:
        all = all.mirror("YZ")
    return all


def main():
    left = make_holder_triangle(True)
    right = make_holder_triangle(False)
    sampler = make_holder_triangle(False).rotate((0, 0, 0), (0, 1, 0), 90) - Workplane(
        "YZ"
    ).rect(200, 200, centered=False).extrude(200).translate((-10, 30, 0))

    ass = cq.Assembly()

    ass.add(left)
    ass.add(right, loc=cq.Location(x=50))
    ass.add(sampler, loc=cq.Location(x=-50))
    show(ass)

    src_dir = Path(__file__).parent
    left.rotate((0, 0, 0), (0, 1, 0), 90).export(str(src_dir / "left.stl"))

    right.rotate((0, 0, 0), (0, 1, 0), 270).export(str(src_dir / "right.stl"))

    # sampler:
    sampler.export(str(src_dir / "sampler.stl"))


if __name__ == "__main__":
    main()
