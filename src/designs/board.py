from ocp_vscode import show

from dtools.primitives.transforms import align
from dtools.texture.hex_grid import HexGridTexture
from dtools.workplane import Workplane


def _create_cutout(angle: float) -> Workplane:
    return (
        Workplane("XY")
        .ellipseArc(16, 15, angle1=180, angle2=360)
        .lineTo(32, -20)
        .lineTo(0, -20)
        .close()
        .extrude(10)
        .rotate_center(axis="Z", angle=angle)
    )


def create_board():
    length = 100
    width = 30
    thickness = 3
    height = 12
    cutout_angle = 30
    magnets_grid = (4, 2)
    magnets_height = 1.0
    magnets_diameter = 10

    curve_points = [
        (0, height),
        (8, 2),
        (10, 1),
        (20, 0),
    ]

    # Create end curve points (mirror of start)
    end_curve_points = [(length - x, y) for x, y in reversed(curve_points)]

    board = (
        Workplane("XZ")
        .moveTo(*curve_points[0])
        .bezier(curve_points)
        .lineTo(*end_curve_points[0])
        .bezier(end_curve_points)
        .offset2D(thickness / 2)
        .extrude(width)
    )
    board = board.edges("|X").fillet(thickness * 0.4)

    left = _create_cutout(-90)
    right = _create_cutout(-270)
    board, left = align(
        board,
        left,
        alignments=(
            "start",
            "center",
            "start",
        ),
    )

    left = left.translate((-5, 0, 4)).rotate_center("Y", cutout_angle)
    board -= left

    right, board = align(
        right,
        board,
        alignments=(
            "end",
            "center",
            "start",
        ),
    )
    right = right.translate((5, 0, 4)).rotate_center("Y", -cutout_angle)
    board -= right

    texture_box = (
        Workplane("XY")
        .box((length - 40) * 1.15, width * 0.92, thickness * 0.8)
        .faces(">Z")
        .texture(HexGridTexture(hex_diameter=6, side_thickness=0.8, hex_height=0.5))
    )
    board, texture_box = align(
        board, texture_box, alignments=("center", "center", "start")
    )
    texture_box = texture_box.translate((0, 0, 0.5))

    board += texture_box

    magnet_holes = (
        Workplane("XY")
        .rarray(
            xCount=magnets_grid[0],
            yCount=magnets_grid[1],
            xSpacing=magnets_diameter + 7,
            ySpacing=magnets_diameter + 5,
        )
        .circle(magnets_diameter / 2 + 0.4)
        .extrude(magnets_height + 0.8)
    )
    board, magnet_holes = align(
        board, magnet_holes, alignments=("center", "center", "start")
    )

    magnet_holes = magnet_holes.translate((0, 0, 0.4))
    board -= magnet_holes

    bbox = board.get_bbox()
    magnet_sampler = board.intersect(
        Workplane("XY").moveTo(bbox.xmin + 25, bbox.ymin + 5).box(12, 18, 10)
    )
    board.export("build/board.stl")
    magnet_sampler.export("build/board_magnet_sampler.stl")
    show(magnet_sampler)


if __name__ == "__main__":
    create_board()
