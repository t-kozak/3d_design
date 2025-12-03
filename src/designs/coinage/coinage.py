from math import sqrt
from pathlib import Path

from cadquery import BoundBox

from dtools.workplane import Workplane

try:
    from ocp_vscode import show  # type: ignore
except ImportError:

    def show(*args, **kwargs):
        pass


def _get_coin_envelope_dims(diameter: float, height: float):
    return (diameter + 4.5, diameter + 4, height + 0.5)


def make_coin_envelope(diameter: float, height: float) -> Workplane:
    assert diameter > 20, "Coin to small -needs to be 20mm+ in diameter"

    box_x, box_y, box_z = _get_coin_envelope_dims(diameter, height)

    envelope = (
        Workplane("XY")
        .rect(box_x, box_y)
        .extrude(box_z)
        .edges("|Z")
        .fillet(4)
        .edges("#Z")
        .chamfer(1)
    )
    envelope -= (
        Workplane("XY")
        .circle(diameter / 2 + 0.2)
        .workplane(offset=height + 1)
        .circle(diameter / 2 + 1.2)
        .loft()
    )

    return envelope


def _make_baton(diameter: float, height: float):
    env_x, env_y, env_z = _get_coin_envelope_dims(diameter, height)
    wall_thickness_xy = 2
    wall_thickness_z = 1.2
    gap_thickness = 0.4

    baton = (
        Workplane("XY")
        .rect(
            (env_x * 2) + gap_thickness + (2 * wall_thickness_xy),
            env_y + (wall_thickness_xy * 2),
        )
        .extrude(env_z + (2 * wall_thickness_z))
        .fillet(1)
    )

    envelope_space = (
        Workplane("XY")
        .rect(env_x + 0.2, env_y + 0.2)
        .extrude(env_z + 0.2)
        .aligned(baton, ("start", "center", "start"))
        .translate((wall_thickness_xy, 0, wall_thickness_z))
    )

    gap = (
        Workplane("XY")
        .rect(gap_thickness, env_y)
        .extrude(wall_thickness_z + env_z / 2)
        .aligned(baton, ("center", "center", "start"))
    )
    baton = baton - gap - envelope_space

    return baton


def _make_diagonal_support_fins(
    bbox, support_height: float, support_length: float, fin_thickness: float
):
    """Create diagonal support fins extending at 45 degrees from both sides"""
    # Left support fin - triangular, extends down-left at 45 degrees
    support_left = (
        Workplane("XY")
        .moveTo(bbox.xmin, bbox.ymin)
        .lineTo(bbox.xmin - support_length, bbox.ymin - support_length)
        .lineTo(bbox.xmin - support_length, bbox.ymin - support_length + fin_thickness)
        .lineTo(bbox.xmin, bbox.ymin + fin_thickness)
        .close()
        .extrude(support_height)
    )

    # Right support fin - triangular, extends down-right at 45 degrees
    support_right = (
        Workplane("XY")
        .moveTo(bbox.xmax, bbox.ymin)
        .lineTo(bbox.xmax + support_length, bbox.ymin - support_length)
        .lineTo(bbox.xmax + support_length, bbox.ymin - support_length + fin_thickness)
        .lineTo(bbox.xmax, bbox.ymin + fin_thickness)
        .close()
        .extrude(support_height)
    )

    return support_left + support_right


def _make_parallel_support_fins(
    bbox_prev, bbox_curr, support_height: float, fin_thickness: float
):
    """Create parallel support fins connecting two adjacent batons"""
    # Calculate Y positions - connect from back of previous to front of current
    y_prev = bbox_prev.ymin
    y_curr = bbox_curr.ymax

    # Left parallel fin connecting the two batons
    x_positions = [
        bbox_prev.xmin + (0.2 * bbox_prev.xlen),
        bbox_prev.xmax - (0.2 * bbox_prev.xlen),
    ]
    fins = Workplane("XY")
    for x_pos in x_positions:
        fins += (
            Workplane("XY")
            .moveTo(x_pos, y_prev)
            .lineTo(x_pos, y_curr)
            .close()
            .offset2D(fin_thickness / 2)
            .extrude(support_height)
        )

    return fins


def _make_edge_fins(
    first_bbox: BoundBox,
    last_bbox: BoundBox,
    support_height: float,
    fin_thickness: float,
    length,
) -> Workplane:
    delta = length * sqrt(2)
    points: list[
        tuple[
            tuple[float, float],
            tuple[float, float],
        ]
    ] = [
        (
            (first_bbox.xmin, first_bbox.ymax),
            (first_bbox.xmin - delta, first_bbox.ymax + delta),
        ),
        (
            (first_bbox.xmax, first_bbox.ymax),
            (first_bbox.xmax + delta, first_bbox.ymax + delta),
        ),
        (
            (last_bbox.xmin, last_bbox.ymin),
            (last_bbox.xmin - delta, last_bbox.ymin - delta),
        ),
        (
            (last_bbox.xmax, last_bbox.ymin),
            (last_bbox.xmax + delta, last_bbox.ymin - delta),
        ),
    ]
    wp = Workplane("XY")
    for pt in points:
        wp += (
            Workplane("XY")
            .move(*pt[0])
            .lineTo(*pt[1])
            .close()
            .offset2D(fin_thickness / 2)
            .extrude(support_height)
        )

    return wp


def make_baton(
    diameter: float, height: float, for_printing: bool = False, copies: int = 1
) -> Workplane:
    if not for_printing:
        return _make_baton(diameter, height)

    # Configuration
    support_height_ratio = 0.9  # Support goes up 60% of baton height

    fin_thickness = 1  # Thickness of all support fins
    baton_spacing = 5  # Gap between batons along Y axis

    # Collect all parts to combine at the end
    all_parts = []

    # # Track the previous baton's bbox for connecting fins
    support_height = 0
    bbox_prev = None

    first_bbox = None
    last_bbox = None

    # Add remaining batons with parallel connecting fins
    for i in range(copies):
        print(f"Builing {i} baton")
        # Create new baton
        new_baton = _make_baton(diameter, height).translate(
            (0, i * baton_spacing, 20 * i)
        )
        bbox = new_baton.get_bbox()
        new_baton = new_baton.rotate(
            (bbox.xmin, bbox.ymin, 0), (bbox.xmax, bbox.ymin, 0), 90
        )

        all_parts.append(new_baton)

        bbox_curr = new_baton.get_bbox()

        # Add parallel fins connecting previous and current baton
        if bbox_prev is not None:
            connecting_fins = _make_parallel_support_fins(
                bbox_prev, bbox_curr, support_height, fin_thickness
            )
            all_parts.append(connecting_fins)

        # Update for next iteration
        if first_bbox is None:
            first_bbox = bbox_curr
        last_bbox = bbox_curr
        bbox_prev = bbox_curr
        support_height = support_height_ratio * bbox_curr.zmax

    assert first_bbox is not None and last_bbox is not None
    all_parts.append(
        _make_edge_fins(first_bbox, last_bbox, support_height, fin_thickness, 15)
    )
    # Combine all parts
    plate = all_parts[0]
    for part in all_parts[1:]:
        plate = plate.union(part)

    return plate


def main():
    Workplane.build_dir = Path("build/coinage")
    sample_coin = (24.7, 2.5)
    sample_coin_envelope = make_coin_envelope(*sample_coin)

    sample_coin_envelope.export("sample_envelope.stl", angularTolerance=0.05)

    # ass = Assembly()

    baton = make_baton(*sample_coin, for_printing=True, copies=1)
    show(baton)
    baton.export("sample_baton.stl")
    # sample_coin_envelope = sample_coin_envelope.aligned(
    #     baton,
    #     ("start", "center", "start"),
    # ).translate((2, 0, 1.2))

    # ass.add(baton, name="baton", color=Color("black"))
    # ass.add(sample_coin_envelope, name="envelope", color=Color("gray"))
    # show(ass)


if __name__ == "__main__":
    main()
