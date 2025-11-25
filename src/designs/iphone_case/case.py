from cadquery import Assembly, BoundBox, Color, Plane
from ocp_vscode import show

from designs.iphone_case.iphone import IPhoneDims, IPhones
from dtools.primitives.transforms import align
from dtools.texture.hex_grid import HexGridTexture
from dtools.texture.linear import LinearTexture
from dtools.workplane import Workplane

# TODO:
# - add carving out a space for screen protector
# - increase the phone_hole to take into account the back skin protector
# - cut out channels for the string
# - chop the thing into 2 pieces
# - change the buttons to be invisible


def _create_phone_mould(iphone: IPhoneDims) -> tuple[Workplane, BoundBox]:
    screen_protector_height = 0.8
    back_skin_height = 0.2

    phone_hole = iphone.get_body_outline().extrude(
        iphone_dims.thickness + back_skin_height + 0.2  # .2 for tolerance
    )
    touch_area_hole = iphone.get_body_outline(scale_x=0.93, scale_y=0.97).extrude(
        iphone_dims.thickness * 1.5
    )
    phone_hole_b_box = phone_hole.get_bbox()
    screen_protector_hole = iphone.get_body_outline(scale_x=0.98, scale_y=0.99).extrude(
        phone_hole_b_box.zlen + screen_protector_height
    )
    phone_hole, touch_area_hole, screen_protector_hole = align(
        phone_hole,
        touch_area_hole,
        screen_protector_hole,
        alignments=("center", "center", "start"),
    )

    cut_out_body = phone_hole + screen_protector_hole + touch_area_hole

    phone_hole_b_box = phone_hole.get_bbox()
    for btn in iphone_dims.buttons_cfg:
        origin_x = 0
        origin_y = phone_hole_b_box.ymax - btn.top_offset
        origin_z = phone_hole_b_box.center.z + 1.2  # no idea
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


def _apply_string_channels(case: Workplane) -> Workplane:
    bbox = case.get_bbox()
    wp = (
        Workplane(Plane.XZ(origin=(bbox.center.x, bbox.ymax, bbox.center.z)))
        .rarray(xSpacing=bbox.xlen * 0.95, ySpacing=10.0, xCount=2, yCount=2)
        .teardrop(radius=1.0)
        .extrude(bbox.ylen * 1.2)
        # .rarray(xSpacing=bbox.xlen * 0.955, ySpacing=1, xCount=2, yCount=1)
        # .teardrop(radius=1.5)
        # .extrude(3)
    )
    return case - wp


def create_iphone_case(iphone: IPhoneDims) -> Workplane:
    back_wall_thickness = iphone.cam_island_cfg.base_to_cam_top_height
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
                edge_width=6.0,
            ),
            cache_key="iphone_case_hex_tex_v4",
        )
        .faces(">Z")
        .texture(
            LinearTexture(height=1),
            cache_key="iphone_case_linear_tex_v1",
        )
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

    body = _apply_string_channels(body)
    return body


# def create_iphone_support_frame(iphone: IPhoneDims):
#     main_body = iphone.get_body_outline().extrude(iphone.thickness)
#     bbox = main_body.get_bbox()
#     hole_dims = (bbox.xlen * 0.85, bbox.ylen * 0.9)
#     hole = Workplane("XY").rect(*hole_dims).extrude(iphone.thickness)
#     main_body, hole = align(main_body, hole,
#           alignments=("center", "center", "center"))
#     main_body -= hole
#     return main_body


if __name__ == "__main__":
    from ocp_vscode import show

    assert show is not None
    iphone_dims = IPhones.IPHONE_16_PRO

    # frame = create_iphone_support_frame(iphone_dims)
    i_case = create_iphone_case(iphone_dims)
    phone = iphone_dims.create()

    ass = Assembly()

    i_case, phone = align(i_case, phone, alignments=("center", "center", "start"))

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
