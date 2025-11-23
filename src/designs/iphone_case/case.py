from cadquery import Assembly, Color

from designs.iphone_case.iphone import IPhoneDims, IPhones
from dtools.primitives.transforms import align
from dtools.texture.hex_grid import HexGridTexture
from dtools.workplane import Workplane


def create_iphone_case(iphone: IPhoneDims) -> Workplane:
    back_wall_thickness = 3.0

    # Create main body
    body = (
        iphone.get_body_outline(scale_x=1.1, scale_y=1.05)
        .extrude(iphone.thickness + 3.0)
        .faces("<Z")
        .texture(
            HexGridTexture(
                hex_diameter=10.0,
                hex_height=back_wall_thickness,
                side_thickness=2,
                solid_edge=True,
            )
        )
        .translate((0, 0, back_wall_thickness))
    )

    phone_hole = iphone.get_body_outline().extrude(iphone_dims.thickness * 1.01)
    phone_outer_hole = iphone.get_body_outline(scale_x=0.93, scale_y=0.97).extrude(
        iphone_dims.thickness * 5
    )
    body, phone_hole, phone_outer_hole = align(
        body, phone_hole, phone_outer_hole, alignments=("center", "center", "start")
    )
    phone_hole = phone_hole.translate((0, 0, 3))
    phone_outer_hole = phone_outer_hole.translate((0, 0, 3))

    phone_hole_b_box = phone_hole.get_bbox()

    body -= phone_hole
    body -= phone_outer_hole

    # Add a cutout for the camera island
    island_outer_scale = 1.015
    island_inner_scale = 1.0
    island_center = iphone_dims.get_cam_island_center(
        scale_x=island_outer_scale,
        scale_y=island_outer_scale,
        offset=(phone_hole_b_box.xmin, phone_hole_b_box.ymin),
    )
    island_center = (island_center[0], island_center[1] - 2)
    island_outer_outline = (
        iphone_dims.get_cam_island_base_outline(
            scale_x=island_outer_scale, scale_y=island_outer_scale
        )
        .extrude(back_wall_thickness)
        .move_center_to(island_center)
    )
    island_inner_outline = (
        iphone_dims.get_cam_island_base_outline(
            scale_x=island_inner_scale, scale_y=island_inner_scale
        )
        .extrude(back_wall_thickness)
        .move_center_to(island_center)
    )
    island_wall = island_outer_outline - island_inner_outline

    body -= island_outer_outline
    body += island_wall

    # Add a cutout for ports and microphones and for easy access to navigation
    # (app switcher gesture)

    body_bbox = body.get_bbox()
    ports_mics_cutout = (
        Workplane("XY")
        .workplane(offset=back_wall_thickness + 2)
        .moveTo(body_bbox.center.x, 0)
        .rect(38, 20)
        .workplane(offset=5)
        .moveTo(body_bbox.center.x, 0)
        .rect(39, 20)
        .workplane(offset=5)
        .moveTo(body_bbox.center.x, 0)
        .rect(42, 20)
        .loft()
    )

    speaker_cutout = (
        Workplane("XY")
        .workplane(offset=back_wall_thickness + 2)
        .moveTo(body_bbox.center.x, body_bbox.ymax)
        .rect(5, 20)
        .workplane(offset=5)
        .moveTo(body_bbox.center.x, body_bbox.ymax)
        .rect(14, 20)
        .workplane(offset=5)
        .moveTo(body_bbox.center.x, body_bbox.ymax)
        .rect(20, 20)
        .loft()
    )

    body -= ports_mics_cutout
    body -= speaker_cutout

    return body


if __name__ == "__main__":
    from ocp_vscode import show

    iphone_dims = IPhones.IPHONE_16_PRO

    i_case = create_iphone_case(iphone_dims)

    phone = iphone_dims.create()

    # Calculate centers for alignment
    phone_center = phone.get_center()
    case_center = i_case.get_center()

    # Z offset: phone 20mm above the case
    z_offset = 20

    ass = Assembly()

    i_case, phone = align(i_case, phone, alignments=("center", "center", "start"))
    # phone = phone.translate((0, 0, 3))
    ass.add(i_case, color=Color("black"), name="case")
    ass.add(
        phone,
        color=Color("gray"),
        name="iPhone",
    )

    i_case.export("build/iphone_case.stl")
    show(ass)
