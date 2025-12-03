from cadquery import Assembly, BoundBox, Color, Location, Plane
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


def _create_phone_mould(
    iphone: IPhoneDims, body_only: bool = False
) -> tuple[Workplane, BoundBox]:
    back_skin_height = 0.2

    assert iphone_dims.screen_protector_height is not None
    phone_hole = iphone.get_body_outline(scale_x=1.01, scale_y=1.01).extrude(9.6)
    touch_area_hole = iphone.get_body_outline(width=64, height=140).extrude(
        iphone_dims.thickness + 10
    )
    phone_hole_b_box = phone_hole.get_bbox()
    phone_hole, touch_area_hole = align(
        phone_hole,
        touch_area_hole,
        alignments=("center", "center", "start"),
    )

    cut_out_body = phone_hole

    if body_only:
        return cut_out_body, phone_hole_b_box

    cut_out_body += touch_area_hole

    phone_hole_b_box = phone_hole.get_bbox()
    for btn in iphone_dims.buttons_cfg:
        origin_x = 0
        origin_y = phone_hole_b_box.ymax - btn.top_offset
        origin_z = phone_hole_b_box.center.z
        if btn.left:
            origin_x = phone_hole_b_box.xmin
            normal = (-1, 0, 0)

        else:
            origin_x = phone_hole_b_box.xmax
            normal = (1, 0, 0)

        space_for_button = (
            Workplane(
                Plane(
                    origin=(origin_x, origin_y, origin_z), normal=normal, xDir=(0, 1, 0)
                )
            )
            .rrect(
                btn.length + 0.6,
                btn.width + 0.6,
                (btn.width + 0.6) / 2.01,
            )
            .extrude(btn.height + 0.2)
        )
        tunnel_for_pressability = (
            Workplane(
                Plane(
                    origin=(origin_x, origin_y, origin_z), normal=normal, xDir=(0, 1, 0)
                )
            )
            .workplane(offset=btn.height)
            .rrect(
                btn.length + 1,
                btn.width + 1,
                (btn.width + 1) / 2.01,
            )
            .extrude(2)
            .faces("|X and <X" if btn.left else "|X and >X")
            .shell(1.5)
        )

        cut_out_body += space_for_button
        cut_out_body += tunnel_for_pressability

    # show(cut_out_body)
    # exit(0)
    return cut_out_body, phone_hole_b_box


def _apply_camera_island(
    body: Workplane, phone_hole_b_box: BoundBox, back_wall_thickness: float
) -> Workplane:
    # Add a cutout for the camera island
    b_box = body.get_bbox()
    island_center = (b_box.xmax - 26, b_box.ymax - 27)
    island_outer_outline = (
        Workplane("XY")
        .moveTo(*island_center)
        .rrect(47, 47, 12)
        .extrude(back_wall_thickness)
    )
    island_inner_outline = (
        Workplane("XY")
        .moveTo(*island_center)
        .rrect(44.5, 44.5, 12)
        .extrude(back_wall_thickness)
    )

    island_wall = island_outer_outline - island_inner_outline

    body -= island_outer_outline
    body += island_wall
    return body


# def _apply_string_channels(case: Workplane) -> Workplane:
#     bbox = case.get_bbox()
#     wp = (
#         Workplane(Plane.XZ(origin=(bbox.center.x, bbox.ymax, bbox.center.z)))
#         .rarray(xSpacing=bbox.xlen * 0.92, ySpacing=10.0, xCount=2, yCount=2)
#         .teardrop(radius=1.0)
#         .extrude(bbox.ylen * 1.2)
#     )
#     return case - wp


def _get_fillet(iphone: IPhoneDims) -> Workplane:
    fillet = (
        iphone.get_body_outline(width=77.8, height=155)
        .extrude(iphone.thickness + 7.0)
        .faces("|Z")
        .fillet(4)
    )

    fillet -= (
        iphone.get_body_outline(width=77.8, height=155)
        .extrude(iphone.thickness)
        .aligned(fillet, ("center", "center", "center"))
    )

    return fillet


def create_iphone_case(iphone: IPhoneDims) -> Workplane:
    back_wall_thickness = iphone.cam_island_cfg.base_to_cam_top_height
    mould, phone_hole_b_box = _create_phone_mould(iphone)
    # Create main body
    body = (
        iphone.get_body_outline(width=78, height=155)
        .extrude(iphone.thickness + 3.0)
        .faces("<Z")
        .texture(
            HexGridTexture(
                hex_diameter=10.0,
                hex_height=back_wall_thickness,
                side_thickness=2,
                edge_width=6.0,
            ),
            cache_key="iphone_case_hex_tex_v5",
        )
        .faces(">Z")
        .texture(
            LinearTexture(height=1),
            cache_key="iphone_case_linear_tex_v2",
        )
        .translate((0, 0, back_wall_thickness))
    )
    body, mould = align(body, mould, alignments=("center", "center", "start"))
    mould = mould.translate((0, 0, back_wall_thickness))
    mould_bbox = mould.get_bbox()
    for btn in iphone.buttons_cfg:
        origin_x = 0
        origin_y = mould_bbox.ymax - btn.top_offset
        origin_z = mould_bbox.center.z - 4.5
        if btn.left:
            origin_x = mould_bbox.xmin + 2
            normal = (-1, 0, 0)
        else:
            origin_x = mould_bbox.xmax - 2
            normal = (1, 0, 0)

        button_indicator = Workplane(
            Plane(origin=(origin_x, origin_y, origin_z), normal=normal, xDir=(0, 1, 0))
        ).sphere(3)
        body += button_indicator

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

    speaker_cutout = (
        Workplane("XY")
        .workplane(offset=back_wall_thickness + iphone.thickness - 2)
        .moveTo(body_bbox.center.x, body_bbox.ymax - 4.5)
        .rect(
            iphone.top_receiver_size[0] + 1,
            iphone.top_receiver_size[1] + 1,
        )
        .extrude(20)
        .edges("|Z")
        .fillet(0.75)
    )

    body -= ports_mics_cutout
    body -= speaker_cutout

    fillet = _get_fillet(iphone).aligned(body, ("center", "center", "center"))
    # body = body.add(fillet)

    return body


if __name__ == "__main__":
    iphone_dims = IPhones.IPHONE_16_PRO
    phone_frame_supports = iphone_dims.get_body_outline().extrude(
        iphone_dims.thickness + 0.3
    )

    frame_hole = (
        Workplane("XY")
        .box(55, 130, 30)
        .edges("|Z")
        .fillet(10)
        .aligned(phone_frame_supports, ("center", "center", "start"))
    )

    phone_frame_supports -= frame_hole
    bbox = phone_frame_supports.get_bbox()
    phone_frame_supports_sampler_neg_area = (
        Workplane("XY")
        .box(bbox.xlen, bbox.ylen - 35, 35)
        .aligned(phone_frame_supports, (("center", "start", "start")))
    )

    support_sampler = phone_frame_supports - phone_frame_supports_sampler_neg_area
    support_sampler.export("build/iphone_case/sample_support.stl")

    i_case = create_iphone_case(iphone_dims)
    phone = iphone_dims.create()

    ass = Assembly()

    i_case, phone = align(i_case, phone, alignments=("center", "center", "start"))

    ass.add(i_case, color=Color("black"), name="case")
    ass.add(phone, color=Color("gray"), name="iPhone", loc=Location((0, 0, 0.2)))
    show(ass)

    i_case.export("build/iphone_case/case.stl")

    case_sampler_box = (
        Workplane("XY").box(30, 45, 50).aligned(i_case, ("start", "end", "start"))
    )

    case_sampler = i_case.intersect(case_sampler_box)
    show(case_sampler)
    case_sampler.export("build/iphone_case/sample_case.stl")
    case_sampler.export("build/iphone_case/case_sampler.stl")
    # ass.add(case_sampler)
    # ass.add(support_sampler, loc=Location((2, 0, 0)))

    # i_case, case_sampler_box = align(
    #     i_case, case_sampler_box, alignments=("start", "end", "center")
    # )
    # case_sampler = i_case.intersect(case_sampler_box)
    # show(case_sampler)
    # # frame, case_sampler_box = align(
    # #     frame, case_sampler_box, alignments=("end", "end", "start")
    # # )
    # # frame_sampler = frame.intersect(case_sampler_box)

    # frame_sampler.export("build/iphone_case/frame_sampler.stl")
