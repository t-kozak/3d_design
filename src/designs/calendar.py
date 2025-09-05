from ctypes import cast
import math
from pathlib import Path
import cadquery as cq
from ocp_vscode import show

from dtools import m_screw
from dtools.dbox import DrawerBoxParams, ParametricDrawerBox
from dtools.texture.hex import HoneycombTexture
from dtools.workplane import Workplane

Workplane.auto_clean = False


class CalMaker:

    base_box_params = DrawerBoxParams(
        content_length=152.0,
        content_width=102.0,
        content_height=15.0,
        box_top_thickness=5.0,
        top_texture=HoneycombTexture(
            hex_side_len=5,
            hex_height_min=0,
            hex_height_max=3,
            height_steps=3,
            rotation_degrees=37.0,
            spacing_coefficient=0.85,
            random_seed=123432,
        ),
    )

    base_to_pillar_screw = m_screw.MScrew.M3
    base_to_pillar_screw_core_length = 10.0
    base_to_pillar_screw_head_height = 3.0
    base_to_pillar_screw_head_height = 3.0

    pillar_base_width = 50.0
    pillar_base_length = 80.0
    pillar_base_side_thickness = 10.0
    pillar_base_top_thickness = 12.0
    pillar_base_hole_depth = 0.4
    pillar_base_clearance = 0.2

    pillar_height = 100.0
    pillar_top_side_len = 20.0

    head_pillar_connector_side = 8.5
    head_pillar_connector_depth = 15.0
    head_pillar_connector_magnet_radius = 5.0 / 2
    head_pillar_connector_magnet_depth = 1.8
    head_pillar_connector_clearance = 0.4

    head_front_side_len = 20.0
    head_front_thickness = 12.0

    head_clip_magnet_radius = 3.92 / 2
    head_clip_magnet_depth = 1.91

    def __init__(self):
        self.base_box = ParametricDrawerBox(self.base_box_params)

    def create_assembly(self) -> cq.Assembly:
        ass = cq.Assembly(name="Calendar")

        base_top = self.__create_base_top()
        base_base = self.base_box.create_box_base()
        drawer = self.base_box.create_drawer()
        pillar = self.__create_pillar()
        head = self.__create_head()
        ass.add(base_base, name="base")
        base_top_vec = cq.Vector(0, 0, base_base.get_bbox().zmax)
        ass.add(
            base_top,
            name="base_top",
            loc=cq.Location(base_top_vec),
        )
        ass.add(
            drawer,
            name="drawer",
            loc=cq.Location(cq.Vector(0, 0, self.base_box_params.box_base_thickness)),
        )

        pillar_xy_loc = base_top.get_center() - pillar.get_center()
        pillar_loc = cq.Vector(
            pillar_xy_loc.x,
            pillar_xy_loc.y,
            base_top_vec.z + base_top.get_bbox().zmax - self.pillar_base_hole_depth,
        )

        ass.add(
            pillar,
            name="pillar",
            loc=cq.Location(pillar_loc),
        )

        pillar_bbox = pillar.get_bbox()
        head_loc = cq.Vector(
            pillar_loc.x + pillar_bbox.xlen / 2,
            pillar_loc.y + 14,
            pillar_loc.z + pillar_bbox.zmax - 16.7,
        )
        ass.add(
            head.rotate_center("Y", 90).rotate_center("Z", 90),
            name="head",
            loc=cq.Location(head_loc),
        )

        return ass

    def export_all_for_printing(self):
        output = Path("build") / "cal"
        output.mkdir(parents=True, exist_ok=True)
        self.__create_head().export(output / "head.stl")

        # Pillar
        pillar = self.__create_pillar()
        (pillar - Workplane("XY").box(1000, 1000, 180)).export(
            output / "sample_pillar_head.stl",
            tolerance=0.01,
            angularTolerance=0.01,
        )
        (pillar.intersect(Workplane("XY").box(1000, 1000, 20))).export(
            output / "sample_pillar_base.stl",
            tolerance=0.01,
            angularTolerance=0.01,
        )

        # Base top
        box_top = self.__create_base_top(for_printing=True)
        translation_vec = box_top.get_center() - pillar.get_center()
        print(f"translation_vec: {translation_vec}")
        (
            box_top.intersect(
                Workplane("XY")
                .moveTo(box_top.get_center().x, box_top.get_center().y)
                .box(pillar.get_bbox().xlen + 3, pillar.get_bbox().ylen + 3, 100)
            )
        ).export(
            output / "sample_base_top.stl",
            tolerance=0.01,
            angularTolerance=0.01,
        )
        box_top.export(output / "base_top.stl")

        # Rest of the base
        self.base_box.create_box_base().export(output / "base_base.stl")
        self.base_box.create_drawer().export(output / "drawer.stl")

    def __create_base_top(self, for_printing: bool = False) -> Workplane:
        top_base = self.base_box.create_box_top()
        base_bbox = top_base.get_bbox()

        center = top_base.get_center()
        pillar_hole_plane_z_offset = (
            self.base_box_params.box_top_thickness - self.pillar_base_hole_depth
        )

        # Create pillar hole at the center of the top face
        pillar_hole = Workplane("XY").workplane(offset=pillar_hole_plane_z_offset)
        pillar_hole = self.__create_pillar_base_shape(
            pillar_hole, with_clearance=True
        ).extrude(100)
        pillar_center = pillar_hole.get_center()
        center_diff = center - pillar_center
        pillar_hole = pillar_hole.translate((center_diff.x, center_diff.y, 0))
        pil_hole_bbox = pillar_hole.get_bbox()
        all = top_base - pillar_hole

        for screw_loc in self.__get_pillar_screw_location(pil_hole_bbox):
            all -= (
                Workplane("XY")
                .moveTo(screw_loc.x, screw_loc.y)
                .screw_hole(
                    self.base_to_pillar_screw,
                    core_length=self.base_to_pillar_screw_core_length,
                    head_height=self.base_to_pillar_screw_head_height,
                    head_on_top=False,
                )
                # .translate((0, 0, -top_base.get_bbox().zlen))
            )

        return all

    def __create_pillar(self) -> Workplane:

        base = self.__create_pillar_base_shape(Workplane("XY"))
        base_b_box = base.get_bbox()
        base = (
            base.workplane(offset=self.pillar_height)
            .moveTo(base_b_box.center.x, base_b_box.center.y)
            .rect(self.pillar_top_side_len, self.pillar_top_side_len)
            .loft()
        )

        for screw_loc in self.__get_pillar_screw_location(base_b_box):
            base -= (
                Workplane("XY")
                .moveTo(screw_loc.x, screw_loc.y)
                .heatsert(
                    self.base_to_pillar_screw,
                    depth=8,
                )
            )

        all = base
        head = (
            Workplane("XY")
            .box(
                self.pillar_top_side_len,
                self.pillar_top_side_len,
                self.pillar_top_side_len / 2,
            )
            .translate(
                (
                    base_b_box.center.x,
                    base_b_box.center.y,
                    self.pillar_height + self.pillar_top_side_len * 0.25,
                )
            )
        )

        head_cylinder = (
            Workplane("XZ")
            .cylinder(self.pillar_top_side_len, self.pillar_top_side_len / 2)
            .translate(
                (
                    base_b_box.center.x,
                    base_b_box.center.y,
                    self.pillar_height + self.pillar_top_side_len * 0.5,
                )
            )
        )
        head_cylinder_center = head_cylinder.get_center()

        hole_for_head = Workplane("XY").box(
            self.head_pillar_connector_side,
            self.head_pillar_connector_depth,
            self.head_pillar_connector_side,
        )

        hole_for_head = hole_for_head.rotate_center("Y", 45).translate(
            (
                head_cylinder_center.x,
                head_cylinder_center.y
                - (self.pillar_top_side_len - self.head_pillar_connector_depth),
                head_cylinder_center.z,
            )
        )

        hole_for_magnet = (
            Workplane("XZ")
            .teardrop(self.head_pillar_connector_magnet_radius)
            .extrude(self.head_pillar_connector_magnet_depth)
            .translate(
                (
                    head_cylinder_center.x,
                    hole_for_head.get_bbox().ymax
                    + self.head_pillar_connector_magnet_depth,
                    head_cylinder_center.z,
                )
            )
        )
        all += head
        all += head_cylinder
        all -= hole_for_head
        all -= hole_for_magnet

        return all

    def __create_head(self) -> Workplane:
        front = (
            Workplane("XY")
            .box(
                self.head_front_side_len,
                self.head_front_side_len,
                self.head_front_thickness,
            )
            .faces()
            .fillet(self.head_front_thickness / 4)
        )

        magnet_hole = (
            Workplane("XZ")
            .teardrop(self.head_clip_magnet_radius)
            .extrude(self.head_clip_magnet_depth)
        )
        front_bbox = front.get_bbox()
        front_center = front_bbox.center
        z_offset = front_bbox.center.z
        magnet_hole = magnet_hole.translate((0, 0, z_offset))
        front -= magnet_hole.translate(
            (
                front_center.x - 4,
                (-self.head_front_side_len / 2) + self.head_clip_magnet_depth,
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x + 4,
                (-self.head_front_side_len) / 2 + self.head_clip_magnet_depth,
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x - 4,
                (self.head_front_side_len / 2),
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x + 4,
                (self.head_front_side_len) / 2,
                0,
            )
        )

        connector = (
            Workplane("XY")
            .box(
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_depth - 2,
            )
            .rotate_center("Z", 45)
            .translate((0, 0, self.head_front_thickness))
        )

        connector_magnet_hole = (
            Workplane("XY")
            .teardrop(self.head_pillar_connector_magnet_radius)
            .extrude(self.head_pillar_connector_magnet_depth)
            .translate(
                (
                    0,
                    0,
                    connector.get_bbox().zmax - self.head_pillar_connector_magnet_depth,
                )
            )
        )

        all = front + connector - connector_magnet_hole
        return all

    def __get_pillar_screw_location(self, bbox: cq.BoundBox) -> list[cq.Vector]:
        return [
            cq.Vector(bbox.xmin + 9, bbox.ymin + 13),
            cq.Vector(bbox.xmax - 9, bbox.ymin + 13),
            cq.Vector(bbox.center.x, bbox.ymax - 7),
        ]

    def __create_pillar_base_shape(
        self, w: Workplane, with_clearance: bool = False
    ) -> Workplane:
        length = self.pillar_base_length
        width = self.pillar_base_width
        side_thickness = self.pillar_base_side_thickness
        top_thickness = self.pillar_base_top_thickness
        if with_clearance:
            length += 2 * self.pillar_base_clearance
            width += 2 * self.pillar_base_clearance
            side_thickness += 2 * self.pillar_base_clearance
            top_thickness += 2 * self.pillar_base_clearance

        return w.parabolic_channel(
            length=length,
            width=width,
            side_thickness=side_thickness,
            top_thickness=top_thickness,
        )


if __name__ == "__main__":

    cal_maker = CalMaker()

    cal_maker.export_all_for_printing()
    show(cal_maker.create_assembly())
