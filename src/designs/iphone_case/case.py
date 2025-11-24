from cadquery import Assembly, BoundBox, Color, Plane
from ocp_vscode import show

from designs.iphone_case.iphone import IPhoneDims, IPhones
from dtools.primitives.transforms import align
from dtools.texture.hex_grid import HexGridTexture
from dtools.texture.linear import LinearTexture
from dtools.workplane import Workplane


def _create_phone_mould(iphone: IPhoneDims) -> tuple[Workplane, BoundBox]:
    phone_hole = iphone.get_body_outline().extrude(iphone_dims.thickness * 1.01)
    phone_outer_hole = iphone.get_body_outline(scale_x=0.93, scale_y=0.97).extrude(
        iphone_dims.thickness * 5
    )
    phone_hole, phone_outer_hole = align(
        phone_hole, phone_outer_hole, alignments=("center", "center", "start")
    )
    phone_hole = phone_hole.translate((0, 0, 3))
    phone_outer_hole = phone_outer_hole.translate((0, 0, 3))

    phone_hole_b_box = phone_hole.get_bbox()

    cut_out_body = phone_hole + phone_outer_hole

    for btn in iphone_dims.buttons_cfg:
        origin_x = 0
        origin_y = phone_hole_b_box.ymax - btn.top_offset
        origin_z = phone_hole_b_box.center.z + 1.35  # no idea why
        if btn.left:
            origin_x = phone_hole_b_box.xmin
            normal = (-1, 0, 0)

        else:
            origin_x = phone_hole_b_box.xmax
            normal = (1, 0, 0)

        cut_out_body += (
            Workplane(
                Plane(
                    origin=(origin_x, origin_y, origin_z), normal=normal, xDir=(0, 1, 0)
                )
            )
            .rrect(
                btn.length + 1,
                btn.width + 1,
                (btn.width + 1) / 2.01,
            )
            .workplane(offset=5)
            .rrect(
                btn.length + 4,
                btn.width + 4,
                (btn.width + 4) / 2.01,
            )
            .loft()
        )

    # show(cut_out_body)
    # raise ValueError()
    return cut_out_body, phone_hole_b_box


def _apply_camera_island(
    body: Workplane, phone_hole_b_box: BoundBox, back_wall_thickness: float
) -> Workplane:
    # Add a cutout for the camera island
    b_box = body.get_bbox()
    island_center = (24, b_box.ymax - 27)
    island_outer_outline = (
        Workplane("XY")
        .moveTo(*island_center)
        .rrect(45, 45, 12)
        .extrude(back_wall_thickness)
    )
    island_inner_outline = (
        Workplane("XY")
        .moveTo(*island_center)
        .rrect(43, 43, 12)
        .extrude(back_wall_thickness)
    )

    island_wall = island_outer_outline - island_inner_outline

    body -= island_outer_outline
    body += island_wall
    return body


def create_iphone_case(iphone: IPhoneDims) -> Workplane:
    back_wall_thickness = 3.0

    mould, phone_hole_b_box = _create_phone_mould(iphone)
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
        .faces(">Z")
        .texture(LinearTexture(height=1))
        .translate((0, 0, back_wall_thickness))
    )

    body, mould = align(body, mould, alignments=("center", "center", "start"))
    mould = mould.translate((0, 0, back_wall_thickness))
    body -= mould

    body = _apply_camera_island(body, phone_hole_b_box, back_wall_thickness)

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
        .workplane(offset=15)
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
        .workplane(offset=15)
        .moveTo(body_bbox.center.x, body_bbox.ymax)
        .rect(20, 20)
        .loft()
    )

    body -= ports_mics_cutout
    body -= speaker_cutout

    return body


# def create_iphone_support_frame(iphone: IPhoneDims):
#     main_body = iphone.get_body_outline().extrude(iphone.thickness)
#     bbox = main_body.get_bbox()
#     hole_dims = (bbox.xlen * 0.85, bbox.ylen * 0.9)
#     hole = Workplane("XY").rect(*hole_dims).extrude(iphone.thickness)
#     main_body, hole = align(main_body, hole, alignments=("center", "center", "center"))
#     main_body -= hole
#     return main_body


if __name__ == "__main__":
    from ocp_vscode import show

    assert show is not None
    iphone_dims = IPhones.IPHONE_16_PRO

    # frame = create_iphone_support_frame(iphone_dims)
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

    case_sampler_box = Workplane("XY").box(20, 20, 50)

    show(ass)

    # i_case, case_sampler_box = align(
    #     i_case, case_sampler_box, alignments=("end", "end", "start")
    # )
    # case_sampler = i_case.intersect(case_sampler_box)
    # frame, case_sampler_box = align(
    #     frame, case_sampler_box, alignments=("end", "end", "start")
    # )
    # frame_sampler = frame.intersect(case_sampler_box)

    # case_sampler.export("build/iphone_case/case_sampler.stl")
    # frame_sampler.export("build/iphone_case/frame_sampler.stl")
